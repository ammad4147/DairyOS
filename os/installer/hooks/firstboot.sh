#!/usr/bin/env bash
set -Eeuo pipefail

DATA_ROOT="/var/lib/dairyos"
APP_ROOT="/opt/dairyos"
WHEELHOUSE="$APP_ROOT/wheelhouse"
SOURCE="$APP_ROOT/source"
ENV_DIR="/etc/dairyos"
MARKER="$DATA_ROOT/.firstboot-complete"

mkdir -p "$DATA_ROOT/storage" "$DATA_ROOT/backups" "$DATA_ROOT/logs" "$ENV_DIR" "$APP_ROOT"

if ! getent group dairyos >/dev/null 2>&1; then
  groupadd --system dairyos
fi
if ! id -u dairyos >/dev/null 2>&1; then
  useradd --system --gid dairyos --home-dir "$DATA_ROOT" --no-create-home dairyos
fi

python3 -m venv "$APP_ROOT/.venv"
"$APP_ROOT/.venv/bin/python" -m pip install --no-index --find-links "$WHEELHOUSE" --upgrade pip setuptools wheel
"$APP_ROOT/.venv/bin/python" -m pip install --no-index --find-links "$WHEELHOUSE" dairyos

if [[ -f "$SOURCE/alembic.ini" ]]; then
  cd "$SOURCE"
  DAIRYOS_DATA_DIR="$DATA_ROOT" "$APP_ROOT/.venv/bin/alembic" upgrade head
fi

chown -R dairyos:dairyos "$DATA_ROOT"

if [[ ! -f "$ENV_DIR/dairyos.env" ]]; then
  umask 077
  cat > "$ENV_DIR/dairyos.env" <<'ENV'
DAIRYOS_DATA_DIR=/var/lib/dairyos
DAIRYOS_HOST=0.0.0.0
DAIRYOS_PORT=8000
DAIRYOS_LOG_LEVEL=info
ENV
fi

if [[ ! -f "$MARKER" ]]; then
  date -u +%Y-%m-%dT%H:%M:%SZ > "$MARKER"
  chown dairyos:dairyos "$MARKER"
fi

systemctl daemon-reload
systemctl enable dairyos.service
