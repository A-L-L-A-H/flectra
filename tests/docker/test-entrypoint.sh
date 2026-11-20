#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENTRYPOINT="$ROOT_DIR/entrypoint.sh"
TMP_DIR="$(mktemp -d)"
MOCK_BIN="$TMP_DIR/bin"

cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$MOCK_BIN" "$TMP_DIR/core-addons/base" "$TMP_DIR/standard-addons" "$TMP_DIR/custom-addons"

cat > "$MOCK_BIN/pg_isready" <<'MOCK'
#!/usr/bin/env bash
exit 0
MOCK

cat > "$MOCK_BIN/psql" <<'MOCK'
#!/usr/bin/env bash
set -Eeuo pipefail

sql=""
while (($#)); do
    case "$1" in
        -c)
            sql="${2:-}"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

case "$sql" in
    *"FROM pg_database"*)
        printf '%s\n' "${TEST_DB_EXISTS:-f}"
        ;;
    *"to_regclass"*)
        printf '%s\n' "${TEST_TABLE_EXISTS:-t}"
        ;;
    *"FROM ir_module_module"*)
        printf '%s\n' "${TEST_BASE_INSTALLED:-t}"
        ;;
    *)
        printf 'Unexpected psql query: %s\n' "$sql" >&2
        exit 2
        ;;
esac
MOCK

cat > "$MOCK_BIN/flectra" <<'MOCK'
#!/usr/bin/env bash
set -Eeuo pipefail

printf '%s\n' "$@" > "$TEST_FLECTRA_ARGS_FILE"

test -f "$FLECTRA_CONF"
grep -q '^addons_path = ' "$FLECTRA_CONF"
grep -q '^data_dir = ' "$FLECTRA_CONF"
grep -q '^db_name = flectra$' "$FLECTRA_CONF"
grep -q '^gevent_port = 8072$' "$FLECTRA_CONF"
grep -q '^list_db = False$' "$FLECTRA_CONF"
grep -q '^default_productivity_apps = True$' "$FLECTRA_CONF"

mode="$(stat -c '%a' "$FLECTRA_CONF")"
[[ "$mode" == "600" ]]
MOCK

chmod +x "$MOCK_BIN/pg_isready" "$MOCK_BIN/psql" "$MOCK_BIN/flectra"

run_entrypoint() {
    local case_name="$1"
    local db_exists="$2"
    local table_exists="$3"
    local base_installed="$4"
    shift 4

    local case_dir="$TMP_DIR/$case_name"
    mkdir -p "$case_dir"

    env \
        PATH="$MOCK_BIN:$PATH" \
        FLECTRA_CONF="$case_dir/flectra.conf" \
        DATA_DIR="$case_dir/data" \
        CORE_ADDONS="$TMP_DIR/core-addons" \
        STANDARD_ADDONS="$TMP_DIR/standard-addons" \
        CUSTOM_ADDONS_DIR="$TMP_DIR/custom-addons" \
        DB_HOST=postgres \
        DB_PORT=5432 \
        DB_USER=flectra \
        DB_PASSWORD=test-db-password \
        DB_NAME=flectra \
        ADMIN_PASSWD=test-master-password \
        HTTP_PORT=8069 \
        GEVENT_PORT=8072 \
        LIST_DB=false \
        DEFAULT_PRODUCTIVITY_APPS=true \
        PROXY_MODE=false \
        TEST_DB_EXISTS="$db_exists" \
        TEST_TABLE_EXISTS="$table_exists" \
        TEST_BASE_INSTALLED="$base_installed" \
        TEST_FLECTRA_ARGS_FILE="$case_dir/args.txt" \
        "$ENTRYPOINT" "$@"

    printf '%s\n' "$case_dir/args.txt"
}

echo "Testing first-boot initialization ..."
first_args="$(run_entrypoint first-boot f f t --data-dir=/tmp/flectra-data)"
grep -Fxq -- '-i' "$first_args"
grep -Fxq -- 'base' "$first_args"
echo "PASS: first boot installs base."

echo "Testing normal startup for an initialized database ..."
normal_args="$(run_entrypoint normal-startup t t t)"
if grep -Fxq -- '-i' "$normal_args"; then
    echo "FAIL: initialized database must not reinstall base." >&2
    exit 1
fi
expected_config_arg="--config=$(dirname "$normal_args")/flectra.conf"
grep -Fxq -- "$expected_config_arg" "$normal_args"
echo "PASS: initialized database starts without reinstalling base."

echo "Testing incomplete database initialization ..."
incomplete_args="$(run_entrypoint incomplete-startup t t f)"
grep -Fxq -- '-i' "$incomplete_args"
grep -Fxq -- 'base' "$incomplete_args"
echo "PASS: database without installed base retries initialization."

echo "All entrypoint tests passed."
