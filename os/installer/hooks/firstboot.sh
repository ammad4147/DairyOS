#!/usr/bin/env bash
set -Eeuo pipefail

DATA_ROOT="/var/lib/dairyos"
APP_ROOT="/opt/dairyos"
WHEELHOUSE="$APP_ROOT/wheelhouse"
SOURCE="$APP_ROOT/source"
ENV_DIR="/etc/dairyos"
ENV_FILE="$ENV_DIR/dairyos.env"
MARKER="$DATA_ROOT/.firstboot-complete"

mkdir -p "$DATA_ROOT/storage" "$DATA_ROOT/backups" "$DATA_ROOT/logs" "$ENV_DIR" "$APP_ROOT"
chmod 0750 "$ENV_DIR"

[[ -d "$WHEELHOUSE" ]] || { echo "ERROR: offline wheelhouse missing: $WHEELHOUSE" >&2; exit 30; }

if ! getent group dairyos >/dev/null 2>&1; then
  groupadd --system dairyos
fi
if ! id -u dairyos >/dev/null 2>&1; then
  useradd --system --gid dairyos --home-dir "$DATA_ROOT" --no-create-home dairyos
fi

systemctl start postgresql

if ! runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='dairyos'" | grep -q 1; then
  DB_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  runuser -u postgres -- psql -v ON_ERROR_STOP=1 -c "CREATE ROLE dairyos LOGIN PASSWORD '${DB_PASSWORD}'"
else
  DB_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  runuser -u postgres -- psql -v ON_ERROR_STOP=1 -c "ALTER ROLE dairyos WITH LOGIN PASSWORD '${DB_PASSWORD}'"
fi

if ! runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_database WHERE datname='dairyos'" | grep -q 1; then
  runuser -u postgres -- createdb -O dairyos dairyos
fi

AUTH_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"

umask 077
cat > "$ENV_FILE" <<ENV
DAIRYOS_ENV=production
DAIRYOS_DATA_DIR=$DATA_ROOT
DAIRYOS_HOST=0.0.0.0
DAIRYOS_PORT=8000
DAIRYOS_LOG_LEVEL=info
DAIRYOS_DB_HOST=127.0.0.1
DAIRYOS_DB_PORT=5432
DAIRYOS_DB_NAME=dairyos
DAIRYOS_DB_USER=dairyos
DAIRYOS_DB_PASSWORD=$DB_PASSWORD
DAIRYOS_AUTH_SECRET=$AUTH_SECRET
ENV
chmod 0600 "$ENV_FILE"

python3 -m venv "$APP_ROOT/.venv"
"$APP_ROOT/.venv/bin/python" -m pip install --no-index --find-links "$WHEELHOUSE" dairyos

if [[ -f "$SOURCE/alembic.ini" ]]; then
  cd "$SOURCE"
  set -a
  source "$ENV_FILE"
  set +a
  "$APP_ROOT/.venv/bin/alembic" upgrade head
fi

chown -R dairyos:dairyos "$DATA_ROOT"

if [[ ! -f "$MARKER" ]]; then
  date -u +%Y-%m-%dT%H:%M:%SZ > "$MARKER"
  chown dairyos:dairyos "$MARKER"
fi

systemctl daemon-reload
systemctl enable dairyos.service
