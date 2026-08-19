#!/usr/bin/env bash
set -Eeuo pipefail

MODE="dry-run"
TARGET_DEVICE=""
DATA_ROOT="/var/lib/dairyos"
MOUNT_ROOT="/mnt/dairyos"
MANIFEST_DIR="/opt/dairyos-os"
PURGE_CONFIRMATION="PURGE DAIRYOS DATA"

usage() {
  cat <<'EOF'
DairyOS installer

Safe default: dry-run. No disk is modified unless all of the following are true:
  --apply
  --target-device /dev/...

Options:
  --target-device DEVICE   Entire target disk, e.g. /dev/sda or /dev/nvme0n1
  --apply                   Actually partition and install
  --dry-run                 Validate only (default)
  --mount-root PATH         Temporary mount root (default /mnt/dairyos)
  --help
EOF
}

require_root() {
  [[ "$(id -u)" -eq 0 ]] || { echo "ERROR: run as root." >&2; exit 20; }
}

require_cmds() {
  local cmd
  for cmd in sfdisk wipefs mkfs.vfat mkfs.ext4 mkswap mount umount debootstrap chroot grub-install update-initramfs systemctl blkid; do
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
  if [[ -b /dev/disk/by-id/dairyos-install-lock ]]; then
    echo "ERROR: installation lock already exists." >&2
    exit 26
  fi
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
  echo "Partition manifest: ${MANIFEST_DIR}/../partitioning/dairyos.sfdisk"
  echo "No disk, filesystem, bootloader, or NVRAM changes will be made."
}

apply_install() {
  partition_nodes
  local staged="${MOUNT_ROOT}/.dairyos-install-staged"
  local committed="${MOUNT_ROOT}/.dairyos-install-committed"
  mkdir -p "$MOUNT_ROOT"
  touch "$MOUNT_ROOT/.install-in-progress"
  trap 'umount -R "$MOUNT_ROOT" 2>/dev/null || true' EXIT

  wipefs -a "$TARGET_DEVICE"
  sfdisk "$TARGET_DEVICE" < "${MANIFEST_DIR}/../partitioning/dairyos.sfdisk"
  partprobe "$TARGET_DEVICE"

  mkfs.vfat -F32 -n DAIRYOS-EFI "$EFI_PART"
  mkfs.ext4 -L DAIRYOS-ROOT "$ROOT_PART"
  mkfs.ext4 -L DAIRYOS-LOG "$LOG_PART"
  mkswap -L DAIRYOS-SWAP "$SWAP_PART"
  mkfs.ext4 -L DAIRYOS-DATA "$DATA_PART"

  mount "$ROOT_PART" "$MOUNT_ROOT"
  mkdir -p "$MOUNT_ROOT/boot/efi" "$MOUNT_ROOT/var/log" "$MOUNT_ROOT/var/lib/dairyos"
  mount "$EFI_PART" "$MOUNT_ROOT/boot/efi"
  mount "$LOG_PART" "$MOUNT_ROOT/var/log"
  mount "$DATA_PART" "$MOUNT_ROOT/var/lib/dairyos"

  debootstrap --arch=amd64 trixie "$MOUNT_ROOT" "https://deb.debian.org/debian"

  cat > "$MOUNT_ROOT/etc/fstab" <<FSTAB
LABEL=DAIRYOS-ROOT / ext4 defaults,errors=remount-ro 0 1
LABEL=DAIRYOS-EFI /boot/efi vfat umask=0077 0 1
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

  chroot "$MOUNT_ROOT" /bin/bash -c '
    set -Eeuo pipefail
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y linux-image-amd64 grub-efi-amd64 grub-pc systemd sudo ca-certificates python3 python3-venv postgresql
    systemctl enable systemd-timesyncd
    mkdir -p /opt/dairyos-os /var/lib/dairyos/backups /var/lib/dairyos/logs /var/lib/dairyos/storage
  '

  cp -a "$(dirname "$0")/../services" "$MOUNT_ROOT/opt/dairyos-os/"
  cp -a "$(dirname "$0")/../config" "$MOUNT_ROOT/opt/dairyos-os/"
  cp -a "$(dirname "$0")/../partitioning" "$MOUNT_ROOT/opt/dairyos-os/"
  cp -a "$(dirname "$0")/../boot" "$MOUNT_ROOT/opt/dairyos-os/"

  chroot "$MOUNT_ROOT" /bin/bash -c '
    set -Eeuo pipefail
    grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=DairyOS --recheck
    grub-install --target=i386-pc "'"$TARGET_DEVICE"'" --recheck
    update-initramfs -c -k all
    systemctl enable dairyos-firstboot.service
  '

  touch "$staged"
  rm -f "$MOUNT_ROOT/.install-in-progress"
  touch "$committed"
  sync
  echo "DairyOS installation committed on ${TARGET_DEVICE}."
}

while (($#)); do
  case "$1" in
    --target-device) TARGET_DEVICE="${2:?missing device}"; shift 2 ;;
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
apply_install
