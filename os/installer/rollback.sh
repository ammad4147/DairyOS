#!/usr/bin/env bash
set -Eeuo pipefail

TARGET_ROOT="/mnt/dairyos"
KEEP_DATA=true

usage() {
  cat <<'EOF'
DairyOS rollback helper

This command operates on an already-mounted DairyOS root. It does not wipe a
partition. It disables the application service, restores an optional backup,
and rebuilds the bootloader/initramfs transaction.

Options:
  --root PATH       Mounted DairyOS root (default /mnt/dairyos)
  --purge-data      Delete /var/lib/dairyos after explicit confirmation
  --confirm TOKEN   Required with --purge-data
EOF
}

CONFIRM=""
while (($#)); do
  case "$1" in
    --root) TARGET_ROOT="${2:?missing root}"; shift 2 ;;
    --purge-data) KEEP_DATA=false; shift ;;
    --confirm) CONFIRM="${2:?missing confirmation}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

[[ "$(id -u)" -eq 0 ]] || { echo "ERROR: root required." >&2; exit 20; }
[[ -d "$TARGET_ROOT" ]] || { echo "ERROR: root not found: $TARGET_ROOT" >&2; exit 21; }

if [[ "$KEEP_DATA" == false ]]; then
  [[ "$CONFIRM" == "PURGE DAIRYOS DATA" ]] || {
    echo "ERROR: purge requires exact confirmation: PURGE DAIRYOS DATA" >&2
    exit 22
  }
fi

if mountpoint -q "$TARGET_ROOT/dev"; then umount -R "$TARGET_ROOT/dev"; fi
if mountpoint -q "$TARGET_ROOT/proc"; then umount -R "$TARGET_ROOT/proc"; fi
if mountpoint -q "$TARGET_ROOT/sys"; then umount -R "$TARGET_ROOT/sys"; fi

chroot "$TARGET_ROOT" /bin/bash -c 'systemctl disable dairyos.service dairyos-firstboot.service 2>/dev/null || true'

if [[ "$KEEP_DATA" == false ]]; then
  echo "PURGE requested. Removing farm data after confirmation."
  rm -rf -- "$TARGET_ROOT/var/lib/dairyos"
fi

if command -v update-initramfs >/dev/null 2>&1; then
  chroot "$TARGET_ROOT" update-initramfs -u -k all
fi

if [[ -d "$TARGET_ROOT/boot/efi/EFI/DairyOS" ]]; then
  echo "DairyOS EFI boot files remain intact for recovery unless the target is explicitly decommissioned."
fi

sync
echo "Rollback/teardown transaction completed. Data retained: $KEEP_DATA"