#!/usr/bin/env bash
set -Eeuo pipefail

OUT_DIR="${1:-dist/os}"
SIGN_KEY_ID="${DAIRYOS_SIGNING_KEY:-}"
mkdir -p "$OUT_DIR"

command -v sha256sum >/dev/null 2>&1 || { echo "ERROR: sha256sum is required." >&2; exit 10; }

MANIFEST="$OUT_DIR/SHA256SUMS"
: > "$MANIFEST"
shopt -s nullglob
for artifact in "$OUT_DIR"/*.iso "$OUT_DIR"/*.img "$OUT_DIR"/*.raw "$OUT_DIR"/*.qcow2; do
  [[ -f "$artifact" ]] || continue
  sha256sum "$artifact" >> "$MANIFEST"
done

[[ -s "$MANIFEST" ]] || { echo "ERROR: no OS image artifacts found." >&2; exit 11; }

if [[ -n "$SIGN_KEY_ID" ]]; then
  command -v gpg >/dev/null 2>&1 || { echo "ERROR: gpg is required when DAIRYOS_SIGNING_KEY is set." >&2; exit 12; }
  gpg --batch --yes --local-user "$SIGN_KEY_ID" --detach-sign --armor --output "$MANIFEST.asc" "$MANIFEST"
  echo "Signed manifest: $MANIFEST.asc"
else
  echo "NOTICE: DAIRYOS_SIGNING_KEY is not set; SHA-256 manifest created but no signature was produced." >&2
fi

cat "$MANIFEST"