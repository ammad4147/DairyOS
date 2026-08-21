#!/usr/bin/env bash
set -Eeuo pipefail

DEST="${1:-/srv/dairyos-debian}"
DIST="trixie"
ARCH="amd64"
MIRROR="https://deb.debian.org/debian"
SECURITY_MIRROR="https://security.debian.org"

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

debmirror \
  --arch="$ARCH" \
  --dist="$DIST-security" \
  --section="main,contrib,non-free,non-free-firmware" \
  --host="$SECURITY_MIRROR" \
  --root=debian-security \
  --method=https \
  --nosource \
  --progress \
  "$DEST/debian-security"

echo "Offline Debian main and security mirrors synchronized to $DEST"
