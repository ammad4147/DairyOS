#!/usr/bin/env bash
set -Eeuo pipefail

TARGET_DEVICE="${1:?Usage: $0 /dev/sdX|/dev/nvme0n1|/dev/mmcblk0}"
RECOVERY_DIR="/var/lib/dairyos-installer"
KEEP_DATA=true

[[ "$(id -u)" -eq 0 ]] || {
  echo "ERROR: root required." >&2
  exit 20
}

[[ -b "$TARGET_DEVICE" ]] || {
  echo "ERROR: target is not a block device: $TARGET_DEVICE" >&2
  exit 21
}

DEVICE_BASENAME="${TARGET_DEVICE##*/}"
case "$DEVICE_BASENAME" in
  sd[a-z]|nvme[0-9]n[0-9]|vd[a-z]|xvd[a-z]) ;;
  *) echo "ERROR: target device is outside approved appliance names: $TARGET_DEVICE" >&2; exit 22 ;;
esac

if [[ "$TARGET_DEVICE" == /dev/nvme* || "$TARGET_DEVICE" == /dev/mmcblk* ]]; then
  SWAP_PART="${TARGET_DEVICE}p5"
  DATA_PART="${TARGET_DEVICE}p6"
else
  SWAP_PART="${TARGET_DEVICE}5"
  DATA_PART="${TARGET_DEVICE}6"
fi

echo "=== DairyOS Rollback/Recovery ==="
echo "Target: $TARGET_DEVICE"

# Check for a partition table backup
PT_BACKUP="${RECOVERY_DIR}/${DEVICE_BASENAME}.pt-backup"
if [[ -f "$PT_BACKUP" ]]; then
  echo "Found partition table backup: $PT_BACKUP"
  read -r -p "Restore original partition table? (y/N): " restore_pt
  if [[ "$restore_pt" =~ ^[Yy]$ ]]; then
    sfdisk "$TARGET_DEVICE" < "$PT_BACKUP"
    partprobe "$TARGET_DEVICE"
    echo "Partition table restored. The system may need a reboot to re-read partitions."
    exit 0
  fi
else
  echo "No partition table backup found. Proceeding with service deactivation and optional data purge."
fi

# Disable services
if mountpoint -q /mnt/dairyos; then
  TARGET_ROOT="/mnt/dairyos"
else
  echo "DairyOS root not mounted; trying to mount..."
  # Attempt to find and mount the root partition
  ROOT_PART=$(blkid -L DAIRYOS-ROOT 2>/dev/null || true)
  if [[ -n "$ROOT_PART" && -b "$ROOT_PART" ]]; then
    mkdir -p /mnt/dairyos
    mount "$ROOT_PART" /mnt/dairyos
    TARGET_ROOT="/mnt/dairyos"
  else
    echo "Could not locate DairyOS root partition. Skipping service deactivation."
    TARGET_ROOT=""
  fi
fi

if [[ -n "$TARGET_ROOT" && -d "$TARGET_ROOT" ]]; then
  chroot "$TARGET_ROOT" /bin/bash -c 'systemctl disable dairyos.service dairyos-firstboot.service 2>/dev/null || true'
fi

# Data purge option
read -r -p "Purge all farm data (/var/lib/dairyos)? (y/N): " purge_data
if [[ "$purge_data" =~ ^[Yy]$ ]]; then
  if [[ -n "$TARGET_ROOT" ]]; then
    rm -rf -- "$TARGET_ROOT/var/lib/dairyos"
    echo "Data purged."
  else
    echo "Cannot purge data: root not mounted."
  fi
fi

if [[ -n "$TARGET_ROOT" ]]; then
  umount -R "$TARGET_ROOT" 2>/dev/null || true
fi

echo "Rollback transaction completed. Data kept: $([ "$purge_data" =~ ^[Yy]$ ] && echo "false" || echo "true")"
