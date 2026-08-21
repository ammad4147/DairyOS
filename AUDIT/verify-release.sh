#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS="$ROOT/AUDIT/results"
mkdir -p "$RESULTS"

exec > >(tee "$RESULTS/release-verification.txt") 2>&1

cd "$ROOT"
OUT_DIR="${OUT_DIR:-$ROOT/dist/os}"
ISO="${ISO:-$OUT_DIR/dairyos-trixie-amd64.iso}"

printf '%s\n' '=== DairyOS release verification ==='
echo "Repository: $ROOT"
echo "Commit: $(git rev-parse HEAD)"
echo "ISO: $ISO"

test -s "$ISO"
test -s "$ISO.sha256"
test -s "$ISO.asc"
test -s "$OUT_DIR/SHA256SUMS"
test -s "$OUT_DIR/SHA256SUMS.asc"

sha256sum -c "$ISO.sha256"
gpg --batch --verify "$ISO.asc" "$ISO"
gpg --batch --verify "$OUT_DIR/SHA256SUMS.asc" "$OUT_DIR/SHA256SUMS"

command -v xorriso >/dev/null
xorriso -indev "$ISO" -report_el_torito plain -report_system_area plain

command -v file >/dev/null
file "$ISO"

echo
printf '%s\n' 'PASS: release checksum, detached-signature, and ISO structure verification completed.'
