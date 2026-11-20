
#!/bin/bash

set -Eeuo pipefail

# ============================================================
# FLECTRA DOCKER ENTRYPOINT
# ============================================================
#
# Responsibilities:
# 1. Resolve Flectra executable.
# 2. Preserve Docker command arguments.
# 3. Load environment configuration.
# 4. Wait for PostgreSQL.
# 5. Generate secure Flectra configuration.
# 6. Detect database initialization.
# 7. Install base module on first boot.
# 8. Start Flectra.
#
# Compatible with:
# - Docker
# - Docker Compose
# - PostgreSQL
# - Flectra 3.x (verify options against your build)
#
# ============================================================


# ------------------------------------------------------------
# 1. Resolve Flectra executable
# ------------------------------------------------------------

FLECTRA_BIN="${FLECTRA_BIN:-}"

case "${1:-}" in
    flectra|flectra-bin)
        FLECTRA_BIN="$1"
        shift
        ;;
    "")
        ;;
    -*)
        # Preserve CLI arguments.
        ;;
    *)
        # Allow custom commands:
        # docker run image bash
        exec "$@"
        ;;
esac


# Automatically detect executable.
if [[ -z "$FLECTRA_BIN" ]]; then

    if command -v flectra >/dev/null 2>&1; then
        FLECTRA_BIN="flectra"

    elif command -v flectra-bin >/dev/null 2>&1; then
        FLECTRA_BIN="flectra-bin"

    else
        echo "ERROR: Flectra executable not found" >&2
        exit 127
    fi

fi


# Validate executable.
if ! command -v "$FLECTRA_BIN" >/dev/null 2>&1; then
    echo "ERROR: Invalid Flectra executable: $FLECTRA_BIN" >&2
    exit 127
fi


# Help/version commands should not require PostgreSQL.
case "${1:-}" in
    --help|-h|--version)
        exec "$FLECTRA_BIN" "$@"
        ;;
esac


# ------------------------------------------------------------
# 2. Environment configuration
# ------------------------------------------------------------

CONF="${FLECTRA_CONF:-/etc/flectra/flectra.conf}"

CORE_ADDONS="${CORE_ADDONS:-/opt/flectra/flectra/addons}"
ADDONS_DIR="${ADDONS_DIR:-/opt/flectra/addons}"

ADDONS_PATH="${ADDONS_PATH:-${CORE_ADDONS},${ADDONS_DIR}}"

DATA_DIR="${DATA_DIR:-/var/lib/flectra}"


# PostgreSQL configuration.
# Supports both new and legacy environment variables.

DB_HOST="${DB_HOST:-${HOST:-db}}"

DB_PORT="${DB_PORT:-${PORT:-5432}}"

DB_USER="${DB_USER:-${POSTGRES_USER:-${USER:-flectra}}}"

DB_PASSWORD="${DB_PASSWORD:-${POSTGRES_PASSWORD:-${PASSWORD:-}}}"

DB_NAME="${DB_NAME:-${DB:-${POSTGRES_DB:-flectra}}}"

DB_MAINTENANCE_DB="${DB_MAINTENANCE_DB:-postgres}"


# Flectra ports.

HTTP_PORT="${HTTP_PORT:-8069}"

GEVENT_PORT="${GEVENT_PORT:-${FLECTRA_GEVENT_PORT:-${LONGPOLL_PORT:-8072}}}"


# Master password.

: "${ADMIN_PASSWD:?ERROR: ADMIN_PASSWD must be configured}"

: "${DB_PASSWORD:?ERROR: DB_PASSWORD or POSTGRES_PASSWORD must be configured}"


# Production defaults.

LIST_DB="${LIST_DB:-True}"


# ------------------------------------------------------------
# 3. Validate configuration
# ------------------------------------------------------------

assert_single_line() {

    local name="$1"
    local value="$2"

    if [[ "$value" == *$'\n'* || "$value" == *$'\r'* ]]; then
        echo "ERROR: ${name} must not contain newline characters" >&2
        exit 1
    fi

}

assert_single_line "FLECTRA_CONF" "$CONF"
assert_single_line "ADDONS_PATH" "$ADDONS_PATH"
assert_single_line "DATA_DIR" "$DATA_DIR"

assert_single_line "DB_HOST" "$DB_HOST"
assert_single_line "DB_PORT" "$DB_PORT"
assert_single_line "DB_USER" "$DB_USER"
assert_single_line "DB_PASSWORD" "$DB_PASSWORD"
assert_single_line "DB_NAME" "$DB_NAME"

assert_single_line "ADMIN_PASSWD" "$ADMIN_PASSWD"

assert_single_line "HTTP_PORT" "$HTTP_PORT"
assert_single_line "GEVENT_PORT" "$GEVENT_PORT"
assert_single_line "LIST_DB" "$LIST_DB"


# Validate ports.
for port in "$DB_PORT" "$HTTP_PORT" "$GEVENT_PORT"; do

    if [[ ! "$port" =~ ^[0-9]+$ ]] || (( port < 1 || port > 65535 )); then
        echo "ERROR: Invalid port: $port" >&2
        exit 1
    fi

done


# ------------------------------------------------------------
# 4. Validate required directories and tools
# ------------------------------------------------------------

mkdir -p "$DATA_DIR"
mkdir -p "$(dirname "$CONF")"

if [[ ! -d "$CORE_ADDONS" ]]; then

    echo "ERROR: Core addons directory does not exist:"
    echo "$CORE_ADDONS" >&2

    exit 1

fi

if [[ ! -d "$ADDONS_DIR" ]]; then
    mkdir -p "$ADDONS_DIR"
fi


for tool in pg_isready psql mktemp; do

    if ! command -v "$tool" >/dev/null 2>&1; then

        echo "ERROR: Required command not found: $tool" >&2

        exit 127

    fi

done


# ------------------------------------------------------------
# 5. Wait for PostgreSQL
# ------------------------------------------------------------

echo
echo "============================================================"
echo " FLECTRA STARTUP"
echo "============================================================"
echo " Flectra executable : $FLECTRA_BIN"
echo " PostgreSQL host    : $DB_HOST"
echo " PostgreSQL port    : $DB_PORT"
echo " PostgreSQL user    : $DB_USER"
echo " Database           : $DB_NAME"
echo " HTTP port          : $HTTP_PORT"
echo " Gevent port        : $GEVENT_PORT"
echo " Data directory     : $DATA_DIR"
echo "============================================================"
echo

echo "Waiting for PostgreSQL ..."

POSTGRES_READY=false

for ((attempt = 1; attempt <= 60; attempt++)); do

    if pg_isready \
        -q \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -t 1; then

        POSTGRES_READY=true
        break

    fi

    echo "PostgreSQL is not ready (${attempt}/60)"

    sleep 1

done


if [[ "$POSTGRES_READY" != "true" ]]; then

    echo "ERROR: PostgreSQL did not become ready" >&2

    exit 1

fi

echo "PostgreSQL is ready."


# ------------------------------------------------------------
# 6. Generate Flectra runtime configuration
# ------------------------------------------------------------

echo "Generating Flectra configuration ..."

umask 077

TMP_CONF="$(mktemp "${CONF}.XXXXXX")"

cleanup() {
    rm -f "$TMP_CONF"
}

trap cleanup EXIT


{
    echo "[options]"

    printf 'addons_path = %s\n' "$ADDONS_PATH"

    # Database configuration.
    printf 'db_host = %s\n' "$DB_HOST"
    printf 'db_port = %s\n' "$DB_PORT"
    printf 'db_user = %s\n' "$DB_USER"
    printf 'db_password = %s\n' "$DB_PASSWORD"
    printf 'db_name = %s\n' "$DB_NAME"

    # HTTP / Gevent.
    printf 'http_port = %s\n' "$HTTP_PORT"
    printf 'gevent_port = %s\n' "$GEVENT_PORT"

    # Data directory.
    printf 'data_dir = %s\n' "$DATA_DIR"

    # Master admin password.
    printf 'admin_passwd = %s\n' "$ADMIN_PASSWD"

    # Database security.
    printf 'list_db = %s\n' "$LIST_DB"

} > "$TMP_CONF"


chmod 600 "$TMP_CONF"

mv -f "$TMP_CONF" "$CONF"

trap - EXIT

echo "Flectra configuration generated."


# ------------------------------------------------------------
# 7. Prepare PostgreSQL connection
# ------------------------------------------------------------

PSQL=(
    psql
    -X
    -w
    -v ON_ERROR_STOP=1
    -h "$DB_HOST"
    -p "$DB_PORT"
    -U "$DB_USER"
)


# ------------------------------------------------------------
# 8. Check if target database exists
# ------------------------------------------------------------

echo "Checking database: $DB_NAME"

if ! DB_EXISTS="$(
    DB_NAME_LIT="${DB_NAME//\'/\'\'}"
    PGPASSWORD="$DB_PASSWORD" \
    "${PSQL[@]}" \
        -d "$DB_MAINTENANCE_DB" \
        -qAt \
        -c "SELECT EXISTS (
            SELECT 1
            FROM pg_database
            WHERE datname = '${DB_NAME_LIT}'
        );"
)"; then

    echo "ERROR: Cannot query PostgreSQL database catalog" >&2
    echo "Check DB_HOST, DB_USER and DB_PASSWORD." >&2

    exit 1

fi


DB_EXISTS="${DB_EXISTS//[[:space:]]/}"

if [[ "$DB_EXISTS" != "t" && "$DB_EXISTS" != "f" ]]; then

    echo "ERROR: Unexpected database existence result" >&2

    exit 1

fi


# ------------------------------------------------------------
# 9. Detect Flectra database initialization
# ------------------------------------------------------------

DB_INITIALIZED=false

if [[ "$DB_EXISTS" == "t" ]]; then

    echo "Database exists. Checking Flectra schema ..."

    # Check module table.

    if ! TABLE_EXISTS="$(
        PGPASSWORD="$DB_PASSWORD" \
        "${PSQL[@]}" \
            -d "$DB_NAME" \
            -qAt \
            -c "SELECT to_regclass('public.ir_module_module') IS NOT NULL;"
    )"; then

        echo "ERROR: Cannot inspect Flectra database schema" >&2

        exit 1

    fi


    TABLE_EXISTS="${TABLE_EXISTS//[[:space:]]/}"


    if [[ "$TABLE_EXISTS" == "t" ]]; then

        echo "Flectra module table found."

        # Verify that base module is installed.

        if ! BASE_INSTALLED="$(
            PGPASSWORD="$DB_PASSWORD" \
            "${PSQL[@]}" \
                -d "$DB_NAME" \
                -qAt \
                -c "SELECT EXISTS (
                    SELECT 1
                    FROM ir_module_module
                    WHERE name = 'base'
                    AND state = 'installed'
                );"
        )"; then

            echo "ERROR: Cannot inspect base module status" >&2

            exit 1

        fi


        BASE_INSTALLED="${BASE_INSTALLED//[[:space:]]/}"


        if [[ "$BASE_INSTALLED" == "t" ]]; then

            DB_INITIALIZED=true

        fi

    fi

else

    echo "Database does not exist yet: $DB_NAME"

fi


# ------------------------------------------------------------
# 10. First boot database initialization
# ------------------------------------------------------------

if [[ "$DB_INITIALIZED" != "true" ]]; then

    echo
    echo "============================================================"
    echo " FIRST BOOT: DATABASE INITIALIZATION"
    echo "============================================================"
    echo " Database: $DB_NAME"
    echo " Module  : base"
    echo "============================================================"
    echo

    echo "Installing Flectra base module ..."

    exec "$FLECTRA_BIN" \
        --config="$CONF" \
        -d "$DB_NAME" \
        -i base \
        "$@"

fi


# ------------------------------------------------------------
# 11. Start Flectra normally
# ------------------------------------------------------------

echo
echo "============================================================"
echo " FLECTRA DATABASE READY"
echo "============================================================"
echo " Database already initialized: $DB_NAME"
echo " Starting Flectra server ..."
echo "============================================================"
echo

exec "$FLECTRA_BIN" \
    --config="$CONF" \
    "$@"
