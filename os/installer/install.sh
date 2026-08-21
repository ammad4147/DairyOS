#!/usr/bin/env bash
set -Eeuo pipefail

MODE="dry-run"
TARGET_DEVICE=""
MOUNT_ROOT="/mnt/dairyos"
MANIFEST_DIR="/opt/dairyos-os"
DEBIAN_MIRROR="file:///srv/dairyos-debian"
RECOVERY_DIR="/var/lib/dairyos-installer"
RECOVERY_STATE=""
PARTITIONING_STARTED=false
INSTALL_COMMITTED=false

cleanup_mounts() {
  umount -R "$MOUNT_ROOT" 2>/dev/null || true
  rm -f /var/lock/dairyos-install.lock 2>/dev/null || true
}

write_recovery_state() {
  local phase="$1"
  mkdir -p "$RECOVERY_DIR"
  RECOVERY_STATE="$RECOVERY_DIR/${TARGET_DEVICE##*/}.state"
  umask 077
  cat > "$RECOVERY_STATE" <<STATE
DairyOS installer recovery state
Target=${TARGET_DEVICE}
Phase=${phase}
Committed=${INSTALL_COMMITTED}
Timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
STATE
}

install_failed() {
  local exit_code=$?
  if (( exit_code != 0 )) && [[ "$INSTALL_COMMITTED" != true ]]; then
    echo "CRITICAL: installation interrupted or failed (code: $exit_code)." >&2
    echo "The target disk is NOT automatically randomized or wiped." >&2
    if [[ -n "$TARGET_DEVICE" ]]; then
      write_recovery_state "failed"
      echo "Recovery state: $RECOVERY_STATE" >&2
    fi
    cleanup_mounts
  fi
  return "$exit_code"
}
trap install_failed ERR
trap cleanup_mounts EXIT

usage() {
  cat <<'EOF'
DairyOS installer

Safe default: dry-run. No disk is modified unless all of the following are true:
  --apply
  --target-device /dev/...

Offline deployment is the default: the Debian 13 (trixie) base repository is
expected at file:///srv/dairyos-debian. A connected installation may override
the mirror explicitly with --debian-mirror https://deb.debian.org/debian.

Options:
  --target-device DEVICE   Entire target disk, e.g. /dev/sda or /dev/nvme0n1
  --debian-mirror URL      Local file mirror or explicitly approved network mirror
  --apply                  Actually partition and install
  --dry-run                Validate only (default)
  --mount-root PATH        Temporary mount root (default /mnt/dairyos)
  --help
EOF
}

require_root() {
  [[ "$(id -u)" -eq 0 ]] || { echo "ERROR: run as root." >&2; exit 20; }
}

require_cmds() {
  local cmd
  for cmd in sfdisk wipefs mkfs.vfat mkfs.ext4 mkswap mount umount debootstrap chroot grub-install update-initramfs systemctl blkid partprobe blockdev; do
    command -v "$cmd" >/dev/null 2>&1 || {
      echo "ERROR: required command not found: $cmd" >&2
      exit 21
    }
  done
}

validate_target() {
  [[ -n "$TARGET_DEVICE" ]] || { echo "ERROR: --target-device is required." >&2; exit 22; }
  [[ -b "$TARGET_DEVICE" ]] || { echo "ERROR: target is not a block device: $TARGET_DEVICE" >&2; exit 23; }
  case "$TARGET_DEVICE" in
    /dev/sda|/dev/sdb|/dev/sdc|/dev/nvme0n1|/dev/vda|/dev/xvda) ;;
    *) echo "ERROR: target device is outside approved appliance names: $TARGET_DEVICE" >&2; exit 24 ;;
  esac
  local size_bytes
  size_bytes="$(blockdev --getsize64 "$TARGET_DEVICE")"
  (( size_bytes >= 32 * 1024 * 1024 * 1024 )) || {
    echo "ERROR: target disk must be at least 32 GiB." >&2
    exit 25
  }
  if [[ -e /var/lock/dairyos-install.lock ]]; then
    echo "ERROR: installation lock already exists." >&2
    exit 26
  fi
}

validate_mirror() {
  case "$DEBIAN_MIRROR" in
    file:///*)
      local path="${DEBIAN_MIRROR#file://}"
      [[ -d "$path" ]] || { echo "ERROR: offline Debian mirror not found: $path" >&2; exit 27; }
      ;;
    https://*|http://*)
      echo "WARNING: connected mirror selected: $DEBIAN_MIRROR" >&2
      ;;
    *)
      echo "ERROR: unsupported Debian mirror URL: $DEBIAN_MIRROR" >&2
      exit 28
      ;;
  esac
}

partition_nodes() {
  case "$TARGET_DEVICE" in
    /dev/nvme*|/dev/mmcblk*)
      EFI_PART="${TARGET_DEVICE}p1"; ROOT_PART="${TARGET_DEVICE}p2"; LOG_PART="${TARGET_DEVICE}p3"; SWAP_PART="${TARGET_DEVICE}p4"; DATA_PART="${TARGET_DEVICE}p5" ;;
    *)
      EFI_PART="${TARGET_DEVICE}1"; ROOT_PART="${TARGET_DEVICE}2"; LOG_PART="${TARGET_DEVICE}3"; SWAP_PART="${TARGET_DEVICE}4"; DATA_PART="${TARGET_DEVICE}5" ;;
  esac
}

run_dry_run() {
  echo "DairyOS installer DRY RUN"
  echo "Target: ${TARGET_DEVICE:-<not supplied>}"
  echo "Debian mirror: $DEBIAN_MIRROR"
  echo "Target release: trixie"
  echo "Partition manifest: ${MANIFEST_DIR}/../partitioning/dairyos.sfdisk"
  echo "No disk, filesystem, bootloader, or NVRAM changes will be made."
}

apply_install() {
  partition_nodes
  local staged="${MOUNT_ROOT}/.dairyos-install-staged"
  local committed="${MOUNT_ROOT}/.dairyos-install-committed"
  mkdir -p "$MOUNT_ROOT"
  install -m 0600 /dev/null /var/lock/dairyos-install.lock
  write_recovery_state "validated"
  touch "$MOUNT_ROOT/.install-in-progress"

  write_recovery_state "partitioning"
  PARTITIONING_STARTED=true
  wipefs -a "$TARGET_DEVICE"
  sfdisk "$TARGET_DEVICE" < "${MANIFEST_DIR}/../partitioning/dairyos.sfdisk"
  partprobe "$TARGET_DEVICE"

  write_recovery_state "filesystems"
  mkfs.vfat -F32 -n DAIRYOS-EFI "$EFI_PART"
  mkfs.ext4 -L DAIRYOS-ROOT "$ROOT_PART"
  mkfs.ext4 -L DAIRYOS-LOG "$LOG_PART"
  mkswap -L DAIRYOS-SWAP "$SWAP_PART"
  mkfs.ext4 -L DAIRYOS-DATA "$DATA_PART"

  mount "$ROOT_PART" "$MOUNT_ROOT"
  mkdir -p "$MOUNT_ROOT/boot/efi" "$MOUNT_ROOT/var/log" "$MOUNT_ROOT/var/log/dairyos" "$MOUNT_ROOT/var/lib/dairyos"
  mount "$EFI_PART" "$MOUNT_ROOT/boot/efi"
  mount "$LOG_PART" "$MOUNT_ROOT/var/log"
  mount "$DATA_PART" "$MOUNT_ROOT/var/lib/dairyos"

  write_recovery_state "base-system"
  debootstrap --arch=amd64 trixie "$MOUNT_ROOT" "$DEBIAN_MIRROR"

  cat > "$MOUNT_ROOT/etc/fstab" <<FSTAB
LABEL=DAIRYOS-ROOT / ext4 defaults,errors=remount-ro 0 1
LABEL=DAIRYOS-EFI /boot/efi vfat umask=0077 0 2
LABEL=DAIRYOS-LOG /var/log ext4 defaults 0 2
LABEL=DAIRYOS-DATA /var/lib/dairyos ext4 defaults 0 2
LABEL=DAIRYOS-SWAP none swap sw 0 0
FSTAB

  cp /etc/resolv.conf "$MOUNT_ROOT/etc/resolv.conf"
  mount --rbind /dev "$MOUNT_ROOT/dev"
  mount --make-rslave "$MOUNT_ROOT/dev"
  mount --rbind /proc "$MOUNT_ROOT/proc"
  mount --make-rslave "$MOUNT_ROOT/proc"
  mount --rbind /sys "$MOUNT_ROOT/sys"
  mount --make-rslave "$MOUNT_ROOT/sys"

  write_recovery_state "packages"
  chroot "$MOUNT_ROOT" /bin/bash -c '
    set -Eeuo pipefail
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y linux-image-amd64 grub-efi-amd64 grub-pc systemd sudo ca-certificates python3 python3-venv postgresql
    systemctl enable systemd-timesyncd
    mkdir -p /opt/dairyos-os /var/lib/dairyos/backups /var/lib/dairyos/logs /var/lib/dairyos/storage /var/log/dairyos
  '

  cp -a "$(dirname "$0")/../services" "$MOUNT_ROOT/opt/dairyos-os/"
  cp -a "$(dirname "$0")/../config" "$MOUNT_ROOT/opt/dairyos-os/"
  cp -a "$(dirname "$0")/../partitioning" "$MOUNT_ROOT/opt/dairyos-os/"
  cp -a "$(dirname "$0")/../boot" "$MOUNT_ROOT/opt/dairyos-os/"

  write_recovery_state "bootloader"
  chroot "$MOUNT_ROOT" /bin/bash -c '
    set -Eeuo pipefail
    grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=DairyOS --recheck
    grub-install --target=i386-pc "'"$TARGET_DEVICE"'" --recheck
    update-initramfs -c -k all
    systemctl enable dairyos-firstboot.service
  '

  touch "$staged"
  rm -f "$MOUNT_ROOT/.install-in-progress"
  INSTALL_COMMITTED=true
  touch "$committed"
  write_recovery_state "committed"
  sync
  echo "DairyOS installation committed on ${TARGET_DEVICE}."
}

while (($#)); do
  case "$1" in
    --target-device) TARGET_DEVICE="${2:?missing device}"; shift 2 ;;
    --debian-mirror) DEBIAN_MIRROR="${2:?missing mirror URL}"; shift 2 ;;
    --apply) MODE="apply"; shift ;;
    --dry-run) MODE="dry-run"; shift ;;
    --mount-root) MOUNT_ROOT="${2:?missing path}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

require_root
require_cmds

if [[ "$MODE" == "dry-run" ]]; then
  run_dry_run
  exit 0
fi

validate_target
validate_mirror
apply_install
