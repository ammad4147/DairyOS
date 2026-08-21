#!/usr/bin/env bash
set -Eeuo pipefail

TARGET_DEVICE="${1:?Usage: $0 /dev/sdX|/dev/nvme0n1|/dev/mmcblk0}"

[[ "$(id -u)" -eq 0 ]] || {
  echo "ERROR: root required." >&2
  exit 20
}

[[ -b "$TARGET_DEVICE" ]] || {
  echo "ERROR: target is not a block device: $TARGET_DEVICE" >&2
  exit 21
}

# Resolve the canonical device basename for explicit target validation.
DEVICE_BASENAME="${TARGET_DEVICE##*/}"

case "$DEVICE_BASENAME" in
  sda|sdb|sdc|nvme0n1|mmcblk0|vda|xvda)
    ;;
  *)
    echo "ERROR: target device is outside approved appliance names: $TARGET_DEVICE" >&2
    exit 22
    ;;
esac

if [[ "$TARGET_DEVICE" == /dev/nvme* || "$TARGET_DEVICE" == /dev/mmcblk* ]]; then
  SWAP_PART="${TARGET_DEVICE}p5"
  DATA_PART="${TARGET_DEVICE}p6"
else
  SWAP_PART="${TARGET_DEVICE}5"
  DATA_PART="${TARGET_DEVICE}6"
fi

echo "=== INITIATING BARE-METAL PURGE ON $TARGET_DEVICE ==="
echo "WARNING: This destroys the DairyOS partition table and farm data."

read -r -p "Type 'PURGE' to confirm: " confirm
[[ "$confirm" == "PURGE" ]] || exit 1

if command -v findmnt >/dev/null 2>&1; then
  while read -r mountpoint; do
    [[ -n "$mountpoint" ]] || continue
    umount -R "$mountpoint" || true
  done < <(
    findmnt -rn -S "$TARGET_DEVICE" -o TARGET | sort -r
  )
fi

if command -v swapoff >/dev/null 2>&1 && [[ -b "$SWAP_PART" ]]; then
  swapoff "$SWAP_PART" 2>/dev/null || true
fi

if command -v efibootmgr >/dev/null 2>&1; then
  BOOT_NUMS=$(
    efibootmgr 2>/dev/null |
      grep "DairyOS" |
      grep -Eo 'Boot[0-9A-F]+' |
      sed 's/Boot//' || true
  )

  for num in $BOOT_NUMS; do
    efibootmgr -b "$num" -B -q || true
  done
fi

if [[ -b "$DATA_PART" ]]; then
  if command -v blkdiscard >/dev/null 2>&1; then
    blkdiscard "$DATA_PART" || true
  elif command -v shred >/dev/null 2>&1; then
    shred -v -n 2 -z "$DATA_PART"
  fi
fi

wipefs -a "$TARGET_DEVICE"

if command -v sgdisk >/dev/null 2>&1; then
  sgdisk --zap-all "$TARGET_DEVICE"
fi

partprobe "$TARGET_DEVICE" || true
sync

echo "=== DAIRYOS NODE PURGED ==="
