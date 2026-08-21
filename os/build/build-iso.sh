#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OS_ROOT="$ROOT/os"
OUT_DIR="${OUT_DIR:-$ROOT/dist/os}"
WORK_DIR="${WORK_DIR:-/var/tmp/dairyos-os-build}"
DIST="trixie"
ARCH="amd64"
DEBIAN_MIRROR="${DEBIAN_MIRROR:-https://deb.debian.org/debian/}"
DEBIAN_SECURITY_MIRROR="${DEBIAN_SECURITY_MIRROR:-https://security.debian.org/debian-security/}"

require_cmd(){ command -v "$1" >/dev/null 2>&1 || { echo "ERROR: required command missing: $1" >&2; exit 10; }; }
for c in lb sha256sum python3 rsync stat; do require_cmd "$c"; done

mkdir -p "$OUT_DIR" "$WORK_DIR"
WORK_FS="$(stat -f -c "%T" "$WORK_DIR")"
case "$WORK_FS" in 9p|v9fs) echo "ERROR: workspace is on Windows-mounted filesystem: $WORK_DIR ($WORK_FS)" >&2; exit 12;; esac

rm -rf "$WORK_DIR/live" "$WORK_DIR/app-stage"
mkdir -p "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os" "$WORK_DIR/live/config/includes.chroot/etc/systemd/system"
"$OS_ROOT/build/stage-app.sh" "$WORK_DIR/app-stage"
mkdir -p "$WORK_DIR/live/config/includes.chroot/opt/dairyos"
cp -a "$WORK_DIR/app-stage/source" "$WORK_DIR/live/config/includes.chroot/opt/dairyos/"
cp -a "$WORK_DIR/app-stage/wheelhouse" "$WORK_DIR/live/config/includes.chroot/opt/dairyos/"
cd "$WORK_DIR/live"

lb config --mode debian --distribution "$DIST" --architectures "$ARCH" --binary-images iso-hybrid --debian-installer live --archive-areas "main contrib non-free-firmware" --apt-indices true --mirror-bootstrap "$DEBIAN_MIRROR" --mirror-chroot "$DEBIAN_MIRROR" --mirror-binary "$DEBIAN_MIRROR" --bootappend-live "boot=live components username=dairyos hostname=dairyos-edge" --iso-application "DairyOS Appliance OS" --iso-publisher "Trident Dairies" --iso-volume "DAIRYOS"

if grep -RniI -E "archive\.ubuntu\.com|security\.ubuntu\.com" config; then echo "ERROR: Ubuntu archive reference detected." >&2; exit 13; fi
grep -RniI "deb.debian.org/debian" config >/dev/null || { echo "ERROR: Debian mirror missing." >&2; exit 14; }

auto_stage=(boot installer partitioning pxe services)
for d in "${auto_stage[@]}"; do cp -a "$OS_ROOT/$d" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/"; done
cp "$OS_ROOT/services/dairyos.service" "$OS_ROOT/services/dairyos-firstboot.service" "$WORK_DIR/live/config/includes.chroot/etc/systemd/system/"
cp "$OS_ROOT/installer/hooks/firstboot.sh" "$OS_ROOT/installer/hooks/validate.sh" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/installer/"

lb build
ISO="$(find "$WORK_DIR/live" -maxdepth 1 -type f -name '*.iso' -print -quit)"
[[ -n "$ISO" ]] || { echo "ERROR: live-build produced no ISO." >&2; exit 20; }
FINAL="$OUT_DIR/dairyos-${DIST}-${ARCH}.iso"
CHECKSUM="$FINAL.sha256"
cp "$ISO" "$FINAL"
sha256sum "$FINAL" > "$CHECKSUM"
"$OS_ROOT/build/release-manifest.sh" "$OUT_DIR"
[[ -f "$FINAL.asc" ]] || { echo "ERROR: release build did not produce detached ISO signature." >&2; exit 21; }
sha256sum "$FINAL"
