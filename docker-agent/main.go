package main

import (
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

const composeProject = "flectra"
const maxOutputBytes = 64 << 10

var backupDir string

type composePS struct {
	Name    string `json:"Name"`
	Service string `json:"Service"`
	State   string `json:"State"`
	Status  string `json:"Status"`
}

type authedHandler func(w http.ResponseWriter, r *http.Request)

func token(next authedHandler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		want := os.Getenv("PANEL_TOKEN")
		got := r.Header.Get("X-Agent-Token")
		if want == "" || subtle.ConstantTimeCompare([]byte(got), []byte(want)) != 1 {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		next(w, r)
	})
}

func compose(args ...string) ([]byte, error) {
	full := append([]string{"compose", "-p", composeProject}, args...)
	cmd := exec.Command("docker", full...)
	out, err := cmd.CombinedOutput()
	return truncateOutput(out), err
}

func truncateOutput(out []byte) []byte {
	if len(out) > maxOutputBytes {
		return out[:maxOutputBytes]
	}
	return out
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func statusHandler(w http.ResponseWriter, r *http.Request) {
	out, err := compose("ps", "--format", "json")
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": string(out)})
		return
	}
	var containers []composePS
	for _, line := range strings.Split(strings.TrimSpace(string(out)), "\n") {
		if line == "" {
			continue
		}
		var c composePS
		if err := json.Unmarshal([]byte(line), &c); err == nil {
			containers = append(containers, c)
		}
	}
	writeJSON(w, http.StatusOK, map[string]any{"containers": containers, "timestamp": time.Now().UTC()})
}

func actionHandler(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Command string `json:"command"`
	}
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20)).Decode(&body); err != nil {
		http.Error(w, "bad body", http.StatusBadRequest)
		return
	}
	var args []string
	switch body.Command {
	case "start":
		args = []string{"up", "-d"}
	case "stop":
		args = []string{"stop"}
	case "restart":
		args = []string{"restart"}
	case "rebuild":
		args = []string{"up", "-d", "--build"}
	default:
		http.Error(w, "unknown command", http.StatusBadRequest)
		return
	}
	out, err := compose(args...)
	writeJSON(w, map[bool]int{true: http.StatusInternalServerError, false: http.StatusOK}[err != nil],
		map[string]string{"output": string(out)})
}

func logsHandler(w http.ResponseWriter, r *http.Request) {
	service := strings.TrimPrefix(r.URL.Path, "/logs/")
	if !regexp.MustCompile(`^[A-Za-z0-9_-]+$`).MatchString(service) {
		http.Error(w, "service required", http.StatusBadRequest)
		return
	}
	tail := r.URL.Query().Get("tail")
	if tail == "" {
		tail = "200"
	}
	tailValue, tailErr := strconv.Atoi(tail)
	if tailErr != nil || tailValue < 1 || tailValue > 5000 {
		http.Error(w, "invalid tail", http.StatusBadRequest)
		return
	}
	out, err := compose("logs", "--tail", tail, service)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": string(out)})
		return
	}
	lines := strings.Split(strings.TrimSpace(string(out)), "\n")
	level := r.URL.Query().Get("level")
	if level != "" {
		if !regexp.MustCompile(`^(INFO|WARNING|ERROR|CRITICAL)$`).MatchString(level) {
			http.Error(w, "invalid level", http.StatusBadRequest)
			return
		}
		var filtered []string
		for _, l := range lines {
			if strings.Contains(l, " - "+level+" ") || strings.Contains(l, level+":") {
				filtered = append(filtered, l)
			}
		}
		lines = filtered
	}
	writeJSON(w, http.StatusOK, map[string]any{"lines": lines})
}

func dbExec(sql string) (string, error) {
	cmd := exec.Command("docker", "compose", "-p", composeProject, "exec", "-T", "db",
		"psql", "-U", os.Getenv("POSTGRES_USER"), "-t", "-A", "-c", sql)
	out, err := cmd.CombinedOutput()
	return string(out), err
}

func databasesHandler(w http.ResponseWriter, r *http.Request) {
	out, err := dbExec("SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database WHERE NOT datistemplate ORDER BY datname")
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": string(out)})
		return
	}
	var dbs []map[string]string
	for _, line := range strings.Split(strings.TrimSpace(out), "\n") {
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, "|", 2)
		if len(parts) == 2 {
			dbs = append(dbs, map[string]string{"name": parts[0], "size": parts[1]})
		}
	}
	writeJSON(w, http.StatusOK, map[string]any{"databases": dbs})
}

func createDropHandler(w http.ResponseWriter, r *http.Request, drop bool) {
	var body struct {
		Name string `json:"name"`
	}
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20)).Decode(&body); err != nil || body.Name == "" {
		http.Error(w, "name required", http.StatusBadRequest)
		return
	}
	if !regexpSafe(body.Name) {
		http.Error(w, "invalid database name", http.StatusBadRequest)
		return
	}
	verb := "CREATE DATABASE"
	if drop {
		verb = "DROP DATABASE IF EXISTS"
	}
	out, err := dbExec(verb + ` "` + body.Name + `"`)
	writeJSON(w, map[bool]int{true: http.StatusInternalServerError, false: http.StatusOK}[err != nil],
		map[string]string{"output": string(out)})
}

func regexpSafe(name string) bool {
	if name == "" || len(name) > 63 {
		return false
	}
	for _, c := range name {
		ok := c == '_' || (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')
		if !ok {
			return false
		}
	}
	return true
}

func backupHandler(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Database string `json:"database"`
	}
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20)).Decode(&body); err != nil || !regexpSafe(body.Database) {
		http.Error(w, "database required", http.StatusBadRequest)
		return
	}
	stamp := time.Now().UTC().Format("20060102T150405Z")
	target := fmt.Sprintf("%s/%s_%s.dump", backupDir, body.Database, stamp)
	cmd := exec.Command("docker", "compose", "-p", composeProject, "exec", "-T", "db",
		"pg_dump", "-U", os.Getenv("POSTGRES_USER"), "-Fc", body.Database)
	outFile, err := os.Create(target)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	defer outFile.Close()
	cmd.Stdout = outFile
	if err := cmd.Run(); err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	fi, _ := os.Stat(target)
	writeJSON(w, http.StatusOK, map[string]any{"file": target, "bytes": fi.Size()})
}

func backupsHandler(w http.ResponseWriter, r *http.Request) {
	entries, err := os.ReadDir(backupDir)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	var files []map[string]any
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".dump") {
			continue
		}
		info, err := e.Info()
		if err != nil {
			log.Printf("skipping backup %s: %v", e.Name(), err)
			continue
		}
		files = append(files, map[string]any{"name": e.Name(), "bytes": info.Size(), "modified": info.ModTime().UTC()})
	}
	sort.Slice(files, func(i, j int) bool { return files[i]["name"].(string) > files[j]["name"].(string) })
	writeJSON(w, http.StatusOK, map[string]any{"backups": files})
}

func restoreHandler(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Filename string `json:"filename"`
		Force    bool   `json:"force"`
	}
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20)).Decode(&body); err != nil || !regexp.MustCompile(`^[A-Za-z0-9_-]+\.dump$`).MatchString(body.Filename) {
		http.Error(w, "invalid filename", http.StatusBadRequest)
		return
	}
	src := filepath.Join(backupDir, body.Filename)
	if clean, err := filepath.Abs(filepath.Clean(src)); err != nil {
		http.Error(w, "invalid filename", http.StatusBadRequest)
		return
	} else {
		root, _ := filepath.Abs(backupDir)
		if !strings.HasPrefix(clean, root+string(filepath.Separator)) {
			http.Error(w, "invalid filename", http.StatusBadRequest)
			return
		}
	}
	if _, err := os.Stat(src); err != nil {
		http.Error(w, "backup not found", http.StatusNotFound)
		return
	}
	dbName := strings.TrimSuffix(body.Filename, ".dump")
	if i := strings.Index(dbName, "_2"); i > 0 {
		dbName = dbName[:i]
	}
	if !regexpSafe(dbName) {
		http.Error(w, "cannot derive database name", http.StatusBadRequest)
		return
	}
	if !body.Force {
		if existing, err := dbExec(fmt.Sprintf(`SELECT 1 FROM pg_database WHERE datname = '%s'`, dbName)); err != nil || strings.TrimSpace(existing) == "" {
			http.Error(w, "database does not exist; use force", http.StatusConflict)
			return
		}
	}
	_, _ = dbExec(fmt.Sprintf(`DROP DATABASE IF EXISTS "%s"`, dbName))
	if out, err := dbExec(fmt.Sprintf(`CREATE DATABASE "%s"`, dbName)); err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": string(out)})
		return
	}
	inFile, err := os.Open(src)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	defer inFile.Close()
	cmd := exec.Command("docker", "compose", "-p", composeProject, "exec", "-T", "db",
		"pg_restore", "-U", os.Getenv("POSTGRES_USER"), "-d", dbName, "--no-owner")
	cmd.Stdin = inFile
	out, err := cmd.CombinedOutput()
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": string(out)})
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"restored": dbName})
}

func retentionHandler(w http.ResponseWriter, r *http.Request) {
	days := 7
	entries, err := os.ReadDir(backupDir)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	cutoff := time.Now().AddDate(0, 0, -days)
	removed := 0
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".dump") {
			continue
		}
		info, err := e.Info()
		if err != nil {
			log.Printf("skipping backup %s: %v", e.Name(), err)
			continue
		}
		if info.ModTime().Before(cutoff) {
			if err := os.Remove(filepath.Join(backupDir, e.Name())); err != nil {
				log.Printf("failed removing backup %s: %v", e.Name(), err)
				continue
			}
			removed++
		}
	}
	writeJSON(w, http.StatusOK, map[string]int{"removed": removed})
}

func main() {
	backupDir = os.Getenv("BACKUP_DIR")
	if backupDir == "" {
		backupDir = "/backups"
	}
	if os.Getenv("PANEL_TOKEN") == "" {
		log.Fatal("PANEL_TOKEN is required")
	}
	mux := http.NewServeMux()
	mux.Handle("GET /status", token(statusHandler))
	mux.Handle("POST /action", token(actionHandler))
	mux.Handle("GET /logs/", token(logsHandler))
	mux.Handle("GET /databases", token(databasesHandler))
	mux.Handle("POST /databases", token(func(w http.ResponseWriter, r *http.Request) { createDropHandler(w, r, false) }))
	mux.Handle("POST /databases/drop", token(func(w http.ResponseWriter, r *http.Request) { createDropHandler(w, r, true) }))
	mux.Handle("POST /backup", token(backupHandler))
	mux.Handle("GET /backups", token(backupsHandler))
	mux.Handle("POST /restore", token(restoreHandler))
	mux.Handle("POST /retention", token(retentionHandler))

	addr := ":8080"
	log.Printf("arsy-agent listening on %s", addr)
	server := &http.Server{
		Addr:              addr,
		Handler:           mux,
		ReadHeaderTimeout: 10 * time.Second,
		ReadTimeout:       30 * time.Second,
		WriteTimeout:      120 * time.Second,
		IdleTimeout:       60 * time.Second,
	}
	log.Fatal(server.ListenAndServe())
}
