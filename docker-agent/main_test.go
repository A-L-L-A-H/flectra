package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
)

func TestRegexpSafe(t *testing.T) {
	for _, name := range []string{"flectra", "db_1", "Db2"} {
		if !regexpSafe(name) {
			t.Fatalf("expected %q valid", name)
		}
	}
	for _, name := range []string{"", "bad-name", "bad;DROP", strings.Repeat("a", 64)} {
		if regexpSafe(name) {
			t.Fatalf("expected %q invalid", name)
		}
	}
}

func TestLogsHandlerValidation(t *testing.T) {
	cases := []struct {
		url    string
		status int
	}{
		{"/logs/../../etc", http.StatusBadRequest},
		{"/logs/app--tail=1", http.StatusBadRequest},
		{"/logs/app?tail=0", http.StatusBadRequest},
		{"/logs/app?tail=5001", http.StatusBadRequest},
		{"/logs/app?level=debug", http.StatusBadRequest},
	}
	for _, tc := range cases {
		req := httptest.NewRequest(http.MethodGet, tc.url, nil)
		rec := httptest.NewRecorder()
		logsHandler(rec, req)
		if rec.Code != tc.status {
			t.Fatalf("%s: got %d want %d", tc.url, rec.Code, tc.status)
		}
	}
}

func TestRestoreHandlerFilenameTraversal(t *testing.T) {
	backupDir = t.TempDir()
	body := strings.NewReader(`{"filename":"../../etc/passwd.dump"}`)
	req := httptest.NewRequest(http.MethodPost, "/restore", body)
	rec := httptest.NewRecorder()
	restoreHandler(rec, req)
	if rec.Code != http.StatusBadRequest {
		t.Fatalf("got %d want %d", rec.Code, http.StatusBadRequest)
	}
}

func TestTokenMiddleware(t *testing.T) {
	os.Setenv("PANEL_TOKEN", "secret")
	handler := token(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/status", nil))
	if rec.Code != http.StatusUnauthorized {
		t.Fatalf("unauthorized: got %d", rec.Code)
	}

	req := httptest.NewRequest(http.MethodGet, "/status", nil)
	req.Header.Set("X-Agent-Token", "secret")
	rec = httptest.NewRecorder()
	handler.ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("valid token: got %d", rec.Code)
	}
	_ = json.Valid([]byte(`{}`))
}
