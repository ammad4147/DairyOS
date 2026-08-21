#!/usr/bin/env bash
set -Eeuo pipefail

OUT_DIR="${1:-dist/os}"
SIGN_KEY_ID="${DAIRYOS_SIGNING_KEY:-}"
ALLOW_UNSIGNED="${DAIRYOS_ALLOW_UNSIGNED:-false}"
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

if [[ -z "$SIGN_KEY_ID" ]]; then
  if [[ "$ALLOW_UNSIGNED" == "true" ]]; then
    echo "WARNING: unsigned development manifest explicitly allowed by DAIRYOS_ALLOW_UNSIGNED=true." >&2
  else
    echo "ERROR: DAIRYOS_SIGNING_KEY is required for a release artifact." >&2
    echo "Set DAIRYOS_ALLOW_UNSIGNED=true only for non-release development output." >&2
    exit 12
  fi
else
  command -v gpg >/dev/null 2>&1 || { echo "ERROR: gpg is required when DAIRYOS_SIGNING_KEY is set." >&2; exit 13; }
  gpg --batch --yes --local-user "$SIGN_KEY_ID" --detach-sign --armor --output "$MANIFEST.asc" "$MANIFEST"
  echo "Signed manifest: $MANIFEST.asc"
fi

cat "$MANIFEST"
