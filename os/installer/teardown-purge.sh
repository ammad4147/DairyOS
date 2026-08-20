#!/usr/bin/env bash
set -Eeuo pipefail

TARGET_DEVICE="${1:?Usage: $0 /dev/sdX}"
[[ "$(id -u)" -eq 0 ]] || { echo "ERROR: root required." >&2; exit 20; }

echo "=== INITIATING BARE-METAL PURGE ON $TARGET_DEVICE ==="
echo "WARNING: This will securely shred veterinary data and destroy the partition table."
read -p "Type 'PURGE' to confirm: " confirm
[[ "$confirm" == "PURGE" ]] || exit 1

BOOT_NUMS=$(efibootmgr | grep "DairyOS" | grep -Eo 'Boot[0-9A-F]+' | sed 's/Boot//')
for num in $BOOT_NUMS; do
    efibootmgr -b "$num" -B -q || true
done

DATA_PART="${TARGET_DEVICE}5"
if [[ -b "$DATA_PART" ]]; then
    shred -v -n 2 -z "$DATA_PART"
fi

wipefs -a "$TARGET_DEVICE"
sgdisk --zap-all "$TARGET_DEVICE"
partprobe "$TARGET_DEVICE"

echo "=== DAIRYOS NODE PURGED ==="
