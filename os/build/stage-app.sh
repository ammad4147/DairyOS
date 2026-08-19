#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="${1:?destination directory is required}"
WHEELHOUSE="$DEST/wheelhouse"
SOURCE="$DEST/source"

command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required." >&2; exit 10; }
python3 -m pip --version >/dev/null 2>&1 || { echo "ERROR: python3 pip is required." >&2; exit 11; }
command -v rsync >/dev/null 2>&1 || { echo "ERROR: rsync is required." >&2; exit 12; }

rm -rf "$DEST"
mkdir -p "$WHEELHOUSE" "$SOURCE"

rsync -a \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude 'node_modules/' \
  --exclude 'audit-results/' \
  --exclude '.os-build/' \
  --exclude 'dist/os/' \
  "$ROOT/" "$SOURCE/"

python3 -m pip wheel --wheel-dir "$WHEELHOUSE" "$SOURCE"

printf 'DairyOS application staging complete.\n'
printf 'Source: %s\n' "$SOURCE"
printf 'Wheelhouse: %s\n' "$WHEELHOUSE"
printf 'Wheel count: %s\n' "$(find "$WHEELHOUSE" -maxdepth 1 -type f -name '*.whl' | wc -l)"