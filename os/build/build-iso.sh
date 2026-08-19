#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OS_ROOT="$ROOT/os"
OUT_DIR="${OUT_DIR:-$ROOT/dist/os}"
WORK_DIR="${WORK_DIR:-$ROOT/.os-build}"
DIST="trixie"
ARCH="amd64"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "ERROR: required command missing: $1" >&2; exit 10; }
}

require_cmd lb
require_cmd sha256sum
require_cmd python3
require_cmd rsync

mkdir -p "$OUT_DIR" "$WORK_DIR"
rm -rf "$WORK_DIR/live" "$WORK_DIR/app-stage"
mkdir -p "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os"
mkdir -p "$WORK_DIR/live/config/includes.chroot/etc/systemd/system"
mkdir -p "$WORK_DIR/live/config/includes.chroot/opt"

"$OS_ROOT/build/stage-app.sh" "$WORK_DIR/app-stage"
mkdir -p "$WORK_DIR/live/config/includes.chroot/opt/dairyos"
cp -a "$WORK_DIR/app-stage/source" "$WORK_DIR/live/config/includes.chroot/opt/dairyos/"
cp -a "$WORK_DIR/app-stage/wheelhouse" "$WORK_DIR/live/config/includes.chroot/opt/dairyos/"

cd "$WORK_DIR/live"

lb config \
  --distribution "$DIST" \
  --architectures "$ARCH" \
  --binary-images iso-hybrid \
  --debian-installer live \
  --archive-areas "main contrib non-free-firmware" \
  --apt-indices true \
  --security true \
  --updates true \
  --bootappend-live "boot=live components username=dairyos hostname=dairyos-edge" \
  --iso-application "DairyOS Appliance OS" \
  --iso-publisher "Trident Dairies" \
  --iso-volume "DAIRYOS" \
  --image-name "dairyos-${DIST}-${ARCH}"

cp -a "$OS_ROOT/boot" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/"
cp -a "$OS_ROOT/config" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/"
cp -a "$OS_ROOT/installer" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/"
cp -a "$OS_ROOT/partitioning" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/"
cp -a "$OS_ROOT/pxe" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/"
cp -a "$OS_ROOT/services" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/"

cp "$OS_ROOT/services/dairyos.service" "$WORK_DIR/live/config/includes.chroot/etc/systemd/system/"
cp "$OS_ROOT/services/dairyos-firstboot.service" "$WORK_DIR/live/config/includes.chroot/etc/systemd/system/"
cp "$OS_ROOT/installer/hooks/firstboot.sh" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/installer/"
cp "$OS_ROOT/installer/hooks/validate.sh" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/installer/"

lb build

ISO="$(find "$WORK_DIR/live" -maxdepth 1 -type f -name '*.iso' -print -quit)"
[[ -n "$ISO" ]] || { echo "ERROR: live-build produced no ISO." >&2; exit 11; }

FINAL="$OUT_DIR/dairyos-${DIST}-${ARCH}.iso"
cp "$ISO" "$FINAL"
sha256sum "$FINAL" > "$FINAL.sha256"

echo "ISO: $FINAL"
echo "SHA256: $FINAL.sha256"
