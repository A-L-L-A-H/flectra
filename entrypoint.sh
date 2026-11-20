#!/bin/bash
set -e

# Translate environment into flectra command-line args.
# Flectra reads config via its own config file / CLI options (Odoo-style).

if [ "$1" = "flectra" ] || [ "${1#-}" != "$1" ]; then
    shift || true
fi

EXTRA_ARGS=()

# database options
if [ -n "$HOST" ]; then EXTRA_ARGS+=("--db_host=$HOST"); fi
if [ -n "$PORT" ]; then EXTRA_ARGS+=("--db_port=$PORT"); fi
if [ -n "$USER" ]; then EXTRA_ARGS+=("--db_user=$USER"); fi
if [ -n "$PASSWORD" ]; then EXTRA_ARGS+=("--db_password=$PASSWORD"); fi
if [ -n "$DB" ]; then EXTRA_ARGS+=("--database=$DB"); fi
if [ -n "$ADMIN_PASSWD" ]; then EXTRA_ARGS+=("--no-database-list" ); EXTRA_ARGS+=("--admin-passwd=$ADMIN_PASSWD" ); fi

# addons path (always include the repo addons dir)
ADDONS_DIR="/opt/flectra/addons"
CORE_ADDONS="/opt/flectra/flectra/addons"
export ADDONS_PATH="${ADDONS_PATH:-${CORE_ADDONS}:${ADDONS_DIR}}"
EXTRA_ARGS+=("--addons-path=$ADDONS_PATH")

# wait for PostgreSQL
if [ -n "$HOST" ]; then
    echo "Waiting for PostgreSQL on ${HOST}:${PORT:-5432} ..."
    for i in $(seq 1 30); do
        if pg_isready -h "$HOST" -p "${PORT:-5432}" -U "${USER:-flectra}" >/dev/null 2>&1; then
            echo "PostgreSQL is up"
            break
        fi
        sleep 1
        if [ "$i" = "30" ]; then
            echo "ERROR: PostgreSQL did not become ready in time" >&2
            exit 1
        fi
    done
fi

exec flectra "${EXTRA_ARGS[@]}" "$@"