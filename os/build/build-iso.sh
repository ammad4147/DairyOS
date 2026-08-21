#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OS_ROOT="$ROOT/os"
OUT_DIR="${OUT_DIR:-$ROOT/dist/os}"
WORK_DIR="${WORK_DIR:-/var/tmp/dairyos-os-build}"

DIST="trixie"
ARCH="amd64"

DEBIAN_MIRROR="https://deb.debian.org/debian/"
DEBIAN_SECURITY_MIRROR="https://security.debian.org/debian-security/"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERROR: required command missing: $1" >&2
    exit 10
  }
}

require_cmd lb
require_cmd sha256sum
require_cmd python3
require_cmd rsync
require_cmd stat

echo "============================================================"
echo " DairyOS ISO BUILD"
echo "============================================================"
echo "Repository : $ROOT"
echo "OS root    : $OS_ROOT"
echo "Output     : $OUT_DIR"
echo "Workspace  : $WORK_DIR"
echo "Distro     : $DIST"
echo "Arch       : $ARCH"
echo "Mirror     : $DEBIAN_MIRROR"
echo "Security   : $DEBIAN_SECURITY_MIRROR"
echo ""

mkdir -p "$OUT_DIR" "$WORK_DIR"

WORK_FS="$(stat -f -c "%T" "$WORK_DIR")"

case "$WORK_FS" in
  9p|v9fs)
    echo "ERROR: Live-Build workspace is on Windows-mounted filesystem: $WORK_DIR ($WORK_FS)" >&2
    echo "Use a WSL-native filesystem such as /var/tmp/dairyos-os-build." >&2
    exit 12
    ;;
esac

echo "Native workspace filesystem: $WORK_FS"

rm -rf \
  "$WORK_DIR/live" \
  "$WORK_DIR/app-stage"

mkdir -p \
  "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os" \
  "$WORK_DIR/live/config/includes.chroot/etc/systemd/system" \
  "$WORK_DIR/live/config/includes.chroot/opt"

echo "=== STAGING APPLICATION ==="
"$OS_ROOT/build/stage-app.sh" "$WORK_DIR/app-stage"

mkdir -p "$WORK_DIR/live/config/includes.chroot/opt/dairyos"

cp -a "$WORK_DIR/app-stage/source" "$WORK_DIR/live/config/includes.chroot/opt/dairyos/"
cp -a "$WORK_DIR/app-stage/wheelhouse" "$WORK_DIR/live/config/includes.chroot/opt/dairyos/"

cd "$WORK_DIR/live"

echo "=== CONFIGURING LIVE-BUILD ==="

lb config \
  --mode debian \
  --distribution "$DIST" \
  --architectures "$ARCH" \
  --binary-images iso-hybrid \
  --debian-installer live \
  --archive-areas "main contrib non-free-firmware" \
  --apt-indices true \
  --mirror-bootstrap "$DEBIAN_MIRROR" \
  --mirror-chroot "$DEBIAN_MIRROR" \
  --mirror-binary "$DEBIAN_MIRROR" \
  --bootappend-live "boot=live components username=dairyos hostname=dairyos-edge" \
  --iso-application "DairyOS Appliance OS" \
  --iso-publisher "Trident Dairies" \
  --iso-volume "DAIRYOS"

echo "=== VERIFYING GENERATED LIVE-BUILD CONFIGURATION ==="

if grep -RniI -E "archive\.ubuntu\.com|security\.ubuntu\.com" config; then
  echo "ERROR: Ubuntu archive reference detected in generated Live-Build configuration." >&2
  exit 13
fi

if ! grep -RniI "deb.debian.org/debian" config >/dev/null 2>&1; then
  echo "ERROR: Debian main mirror was not written into Live-Build configuration." >&2
  exit 14
fi

echo "PASS: Debian main mirror configured."

if grep -RniI "security.debian.org/debian-security" config >/dev/null 2>&1; then
  echo "PASS: Debian security mirror configured."
else
  echo "WARNING: Debian security mirror was not explicitly emitted by this Live-Build release."
fi

echo "=== LIVE-BUILD CONFIG SNAPSHOT ==="
grep -RniI -E "mirror|archive|security" config || true

echo "=== STAGING OS HANDOVER ARTIFACTS ==="

cp -a "$OS_ROOT/boot" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/"
cp -a "$OS_ROOT/installer" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/"
cp -a "$OS_ROOT/partitioning" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/"
cp -a "$OS_ROOT/pxe" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/"
cp -a "$OS_ROOT/services" "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/"

cp "$OS_ROOT/services/dairyos.service" \
   "$WORK_DIR/live/config/includes.chroot/etc/systemd/system/"

cp "$OS_ROOT/services/dairyos-firstboot.service" \
   "$WORK_DIR/live/config/includes.chroot/etc/systemd/system/"

cp "$OS_ROOT/installer/hooks/firstboot.sh" \
   "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/installer/"

cp "$OS_ROOT/installer/hooks/validate.sh" \
   "$WORK_DIR/live/config/includes.chroot/opt/dairyos-os/installer/"

echo "=== BUILDING ISO ==="

lb build

ISO="$(find "$WORK_DIR/live" -maxdepth 1 -type f -name "*.iso" -print -quit)"

if [[ -z "$ISO" ]]; then
  echo "ERROR: live-build produced no ISO." >&2
  exit 20
fi

FINAL="$OUT_DIR/dairyos-${DIST}-${ARCH}.iso"
CHECKSUM="$FINAL.sha256"

rm -f "$FINAL" "$CHECKSUM"
cp "$ISO" "$FINAL"
sha256sum "$FINAL" > "$CHECKSUM"

echo "=== GENERATING RELEASE MANIFEST ==="
"$OS_ROOT/build/release-manifest.sh" "$OUT_DIR"

echo ""
echo "============================================================"
echo " BUILD COMPLETE"
echo "============================================================"
echo "ISO    : $FINAL"
echo "SHA256 : $CHECKSUM"
echo ""
sha256sum "$FINAL"
