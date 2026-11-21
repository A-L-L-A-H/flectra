#!/usr/bin/env bash

# Give an actionable error when the script is mistakenly invoked with /bin/sh.
if [ -z "${BASH_VERSION:-}" ]; then
    printf '%s\n' "ERROR: entrypoint.sh requires Bash; use ENTRYPOINT [\"/bin/bash\", \"/entrypoint.sh\"]." >&2
    exit 2
fi

set -Eeuo pipefail

# ============================================================
# FLECTRA DOCKER ENTRYPOINT
# ============================================================

# ------------------------------------------------------------
# 1. Resolve executable and preserve Docker arguments
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
        # The default executable will be resolved below. Keep all options.
        ;;
    *)
        # Support commands such as: docker run IMAGE bash
        exec "$@"
        ;;
esac

if [[ -z "$FLECTRA_BIN" ]]; then
    if command -v flectra >/dev/null 2>&1; then
        FLECTRA_BIN="flectra"
    elif command -v flectra-bin >/dev/null 2>&1; then
        FLECTRA_BIN="flectra-bin"
    else
        echo "ERROR: Flectra executable not found (expected flectra or flectra-bin)." >&2
        exit 127
    fi
fi

if ! command -v "$FLECTRA_BIN" >/dev/null 2>&1; then
    echo "ERROR: Flectra executable is not available: $FLECTRA_BIN" >&2
    exit 127
fi

# Informational commands must work without database secrets or PostgreSQL.
case "${1:-}" in
    --help|-h|--version)
        exec "$FLECTRA_BIN" "$@"
        ;;
esac


# ------------------------------------------------------------
# 2. Runtime configuration
# ------------------------------------------------------------

CONF="${FLECTRA_CONF:-/etc/flectra/flectra.conf}"
DATA_DIR="${DATA_DIR:-/var/lib/flectra}"

# Flectra's internal addons include the base module. The source
# repository's top-level addons directory contains standard apps.
CORE_ADDONS="${CORE_ADDONS:-/opt/flectra/flectra/addons}"
STANDARD_ADDONS="${STANDARD_ADDONS:-${ADDONS_DIR:-/opt/flectra/addons}}"
CUSTOM_ADDONS_DIR="${CUSTOM_ADDONS_DIR:-/opt/flectra/custom-addons}"

ADDONS_PATH="${ADDONS_PATH:-${CORE_ADDONS},${STANDARD_ADDONS},${CUSTOM_ADDONS_DIR}}"

# Support both the current names and the legacy Docker variables.
DB_HOST="${DB_HOST:-${HOST:-db}}"
DB_PORT="${DB_PORT:-${PORT:-5432}}"
DB_USER="${DB_USER:-${POSTGRES_USER:-${USER:-flectra}}}"
DB_PASSWORD="${DB_PASSWORD:-${POSTGRES_PASSWORD:-${PASSWORD:-}}}"
DB_NAME="${DB_NAME:-${DB:-${POSTGRES_DB:-flectra}}}"
DB_MAINTENANCE_DB="${DB_MAINTENANCE_DB:-postgres}"

HTTP_PORT="${HTTP_PORT:-8069}"
GEVENT_PORT="${GEVENT_PORT:-${FLECTRA_GEVENT_PORT:-${LONGPOLL_PORT:-8072}}}"

: "${ADMIN_PASSWD:?ERROR: ADMIN_PASSWD must be set}"
: "${DB_PASSWORD:?ERROR: DB_PASSWORD (or POSTGRES_PASSWORD) must be set}"

normalize_bool() {
    local name="$1"
    local value="${2,,}"

    case "$value" in
        true|1|yes|on)
            printf 'True'
            ;;
        false|0|no|off|'')
            printf 'False'
            ;;
        *)
            printf 'ERROR: %s must be true or false (received: %s)\n' "$name" "$2" >&2
            return 1
            ;;
    esac
}

LIST_DB="$(normalize_bool LIST_DB "${LIST_DB:-false}")"
DEFAULT_PRODUCTIVITY_APPS="$(normalize_bool DEFAULT_PRODUCTIVITY_APPS "${DEFAULT_PRODUCTIVITY_APPS:-false}")"
PROXY_MODE="$(normalize_bool PROXY_MODE "${PROXY_MODE:-false}")"


# ------------------------------------------------------------
# 3. Validate configuration before writing it
# ------------------------------------------------------------

assert_single_line() {
    local name="$1"
    local value="$2"

    if [[ "$value" == *$'\n'* || "$value" == *$'\r'* ]]; then
        echo "ERROR: $name must not contain newline characters." >&2
        exit 1
    fi
}

assert_single_line FLECTRA_CONF "$CONF"
assert_single_line DATA_DIR "$DATA_DIR"
assert_single_line ADDONS_PATH "$ADDONS_PATH"
assert_single_line CORE_ADDONS "$CORE_ADDONS"
assert_single_line STANDARD_ADDONS "$STANDARD_ADDONS"
assert_single_line CUSTOM_ADDONS_DIR "$CUSTOM_ADDONS_DIR"
assert_single_line DB_HOST "$DB_HOST"
assert_single_line DB_PORT "$DB_PORT"
assert_single_line DB_USER "$DB_USER"
assert_single_line DB_PASSWORD "$DB_PASSWORD"
assert_single_line DB_NAME "$DB_NAME"
assert_single_line DB_MAINTENANCE_DB "$DB_MAINTENANCE_DB"
assert_single_line ADMIN_PASSWD "$ADMIN_PASSWD"
assert_single_line HTTP_PORT "$HTTP_PORT"
assert_single_line GEVENT_PORT "$GEVENT_PORT"

validate_port() {
    local name="$1"
    local value="$2"

    if [[ ! "$value" =~ ^[0-9]{1,5}$ ]] || (( 10#$value < 1 || 10#$value > 65535 )); then
        echo "ERROR: $name must be a TCP port between 1 and 65535 (received: $value)." >&2
        exit 1
    fi
}

validate_port DB_PORT "$DB_PORT"
validate_port HTTP_PORT "$HTTP_PORT"
validate_port GEVENT_PORT "$GEVENT_PORT"

if [[ -z "$DB_NAME" || -z "$DB_USER" || -z "$DB_HOST" ]]; then
    echo "ERROR: DB_NAME, DB_USER and DB_HOST must not be empty." >&2
    exit 1
fi


# ------------------------------------------------------------
# 4. Validate runtime directories and required tools
# ------------------------------------------------------------

for tool in pg_isready psql mktemp; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "ERROR: Required command not found: $tool" >&2
        exit 127
    fi
done

if [[ ! -d "$CORE_ADDONS" || ! -d "$CORE_ADDONS/base" ]]; then
    echo "ERROR: Flectra core addons or base module not found: $CORE_ADDONS" >&2
    exit 1
fi

if [[ ! -d "$STANDARD_ADDONS" ]]; then
    echo "ERROR: Standard addons directory not found: $STANDARD_ADDONS" >&2
    exit 1
fi

mkdir -p "$CUSTOM_ADDONS_DIR" "$DATA_DIR" "$(dirname "$CONF")"

if [[ ! -w "$DATA_DIR" ]]; then
    echo "ERROR: Flectra data directory is not writable by $(id -un): $DATA_DIR" >&2
    exit 1
fi

if [[ ! -w "$(dirname "$CONF")" ]]; then
    echo "ERROR: Flectra configuration directory is not writable: $(dirname "$CONF")" >&2
    exit 1
fi


# ------------------------------------------------------------
# 5. Wait for PostgreSQL
# ------------------------------------------------------------

echo
echo "============================================================"
echo " FLECTRA STARTUP"
echo "============================================================"
echo " Executable          : $FLECTRA_BIN"
echo " PostgreSQL host     : $DB_HOST"
echo " PostgreSQL port     : $DB_PORT"
echo " PostgreSQL user     : $DB_USER"
echo " Database            : $DB_NAME"
echo " HTTP port           : $HTTP_PORT"
echo " Gevent port         : $GEVENT_PORT"
echo " Data directory      : $DATA_DIR"
echo "============================================================"
echo
echo "Waiting for PostgreSQL ..."

POSTGRES_READY=false

for ((attempt = 1; attempt <= 60; attempt++)); do
    if pg_isready -q -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -t 1; then
        POSTGRES_READY=true
        break
    fi

    echo "PostgreSQL is not ready ($attempt/60)"
    sleep 1
done

if [[ "$POSTGRES_READY" != "true" ]]; then
    echo "ERROR: PostgreSQL did not become ready at $DB_HOST:$DB_PORT within 60 seconds." >&2
    exit 1
fi

echo "PostgreSQL is ready."


# ------------------------------------------------------------
# 6. Render runtime configuration atomically
# ------------------------------------------------------------

echo "Generating Flectra configuration ..."

umask 077
TMP_CONF="$(mktemp "${CONF}.XXXXXX")"

cleanup() {
    rm -f "$TMP_CONF"
}
trap cleanup EXIT

{
    printf '[options]\n'
    printf 'addons_path = %s\n' "$ADDONS_PATH"

    printf 'data_dir = %s\n' "$DATA_DIR"

    printf 'db_host = %s\n' "$DB_HOST"
    printf 'db_port = %s\n' "$DB_PORT"
    printf 'db_user = %s\n' "$DB_USER"
    printf 'db_password = %s\n' "$DB_PASSWORD"
    printf 'db_name = %s\n' "$DB_NAME"

    printf 'http_port = %s\n' "$HTTP_PORT"
    printf 'gevent_port = %s\n' "$GEVENT_PORT"

    printf 'admin_passwd = %s\n' "$ADMIN_PASSWD"
    printf 'list_db = %s\n' "$LIST_DB"
    printf 'default_productivity_apps = %s\n' "$DEFAULT_PRODUCTIVITY_APPS"
    printf 'proxy_mode = %s\n' "$PROXY_MODE"
} > "$TMP_CONF"

chmod 0600 "$TMP_CONF"
mv -f "$TMP_CONF" "$CONF"
trap - EXIT

echo "Flectra configuration generated (permissions: 0600)."


# ------------------------------------------------------------
# 7. PostgreSQL query helper
# ------------------------------------------------------------

psql_query() {
    local database="$1"
    shift

    PGPASSWORD="$DB_PASSWORD" psql         -X         -w         -v ON_ERROR_STOP=1         -h "$DB_HOST"         -p "$DB_PORT"         -U "$DB_USER"         -d "$database"         "$@"
}


# ------------------------------------------------------------
# 8. Check whether the target database exists
# ------------------------------------------------------------

echo "Checking database: $DB_NAME"

if ! DB_EXISTS="$(
    psql_query "$DB_MAINTENANCE_DB"         -qAt         -v "target_db=$DB_NAME"         -c "SELECT EXISTS (
            SELECT 1
            FROM pg_database
            WHERE datname = :'target_db'
        );"
)"; then
    echo "ERROR: Cannot query PostgreSQL database catalog. Check DB credentials and permissions." >&2
    exit 1
fi

DB_EXISTS="${DB_EXISTS//[[:space:]]/}"

if [[ "$DB_EXISTS" != "t" && "$DB_EXISTS" != "f" ]]; then
    echo "ERROR: Unexpected PostgreSQL database existence result: $DB_EXISTS" >&2
    exit 1
fi


# ------------------------------------------------------------
# 9. Detect whether Flectra base is installed
# ------------------------------------------------------------

DB_INITIALIZED=false

if [[ "$DB_EXISTS" == "t" ]]; then
    echo "Database exists. Checking Flectra schema ..."

    if ! TABLE_EXISTS="$(
        psql_query "$DB_NAME"             -qAt             -c "SELECT to_regclass('public.ir_module_module') IS NOT NULL;"
    )"; then
        echo "ERROR: Cannot inspect Flectra schema in database $DB_NAME." >&2
        exit 1
    fi

    TABLE_EXISTS="${TABLE_EXISTS//[[:space:]]/}"

    if [[ "$TABLE_EXISTS" == "t" ]]; then
        if ! BASE_INSTALLED="$(
            psql_query "$DB_NAME"                 -qAt                 -c "SELECT EXISTS (
                    SELECT 1
                    FROM ir_module_module
                    WHERE name = 'base'
                      AND state = 'installed'
                );"
        )"; then
            echo "ERROR: Cannot inspect base module state in database $DB_NAME." >&2
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
# 10. Initialize an empty database exactly on first boot
# ------------------------------------------------------------

if [[ "$DB_INITIALIZED" != "true" ]]; then
    echo
    echo "============================================================"
    echo " FIRST BOOT: DATABASE INITIALIZATION"
    echo "============================================================"
    echo " Database: $DB_NAME"
    echo " Module  : base"
    echo "============================================================"
    echo "Installing Flectra base module ..."

    exec "$FLECTRA_BIN"         --config="$CONF"         -d "$DB_NAME"         -i base         "$@"
fi


# ------------------------------------------------------------
# 11. Start the initialized database normally
# ------------------------------------------------------------

echo
echo "============================================================"
echo " FLECTRA DATABASE READY"
echo "============================================================"
echo " Database already initialized: $DB_NAME"
echo " Starting Flectra server ..."
echo "============================================================"

exec "$FLECTRA_BIN"     --config="$CONF"     "$@"
