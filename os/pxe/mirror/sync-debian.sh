#!/usr/bin/env bash
set -Eeuo pipefail

DEST="${1:-/srv/dairyos-debian}"
DIST="trixie"
ARCH="amd64"
MIRROR="https://deb.debian.org/debian"

command -v debmirror >/dev/null 2>&1 || {
  echo "ERROR: install debmirror on the mirror host." >&2
  exit 10
}

mkdir -p "$DEST"

debmirror \
  --arch="$ARCH" \
  --dist="$DIST" \
  --section="main,contrib,non-free,non-free-firmware" \
  --host="$MIRROR" \
  --root=debian \
  --method=https \
  --nosource \
  --progress \
  "$DEST"

echo "Offline Debian mirror synchronized to $DEST"
