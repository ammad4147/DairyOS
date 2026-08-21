#!/usr/bin/env bash
set -Eeuo pipefail

OUT_DIR="${1:-dist/os}"
SIGN_KEY_ID="${DAIRYOS_SIGNING_KEY:-}"
DAIRYOS_ALLOW_UNSIGNED="false"
ALLOW_UNSIGNED="${DAIRYOS_ALLOW_UNSIGNED:-false}"

mkdir -p "$OUT_DIR"

command -v sha256sum >/dev/null 2>&1 || {
  echo "ERROR: sha256sum is required." >&2
  exit 10
}

MANIFEST="$OUT_DIR/SHA256SUMS"
: > "$MANIFEST"

shopt -s nullglob

for artifact in \
  "$OUT_DIR"/*.iso \
  "$OUT_DIR"/*.img \
  "$OUT_DIR"/*.raw \
  "$OUT_DIR"/*.qcow2
do
  [[ -f "$artifact" ]] || continue
  sha256sum "$artifact" >> "$MANIFEST"
done

[[ -s "$MANIFEST" ]] || {
  echo "ERROR: no OS image artifacts found." >&2
  exit 11
}

# A production release must be cryptographically signed.
# Unsigned output is intentionally disabled by default and must only
# be enabled explicitly by changing this policy at invocation time.
if [[ -z "$SIGN_KEY_ID" ]]; then
  [[ "$ALLOW_UNSIGNED" == "true" ]] || {
    echo "ERROR: DAIRYOS_SIGNING_KEY is required for release output." >&2
    exit 12
  }

  echo "WARNING: unsigned development output explicitly enabled." >&2
else
  command -v gpg >/dev/null 2>&1 || {
    echo "ERROR: gpg required." >&2
    exit 13
  }

  gpg \
    --batch \
    --yes \
    --local-user "$SIGN_KEY_ID" \
    --detach-sign \
    --armor \
    --output "$MANIFEST.asc" \
    "$MANIFEST"

  for iso in "$OUT_DIR"/*.iso; do
    [[ -f "$iso" ]] || continue

    gpg \
      --batch \
      --yes \
      --local-user "$SIGN_KEY_ID" \
      --detach-sign \
      --armor \
      --output "$iso.asc" \
      "$iso"
  done

  gpg \
    --batch \
    --verify \
    "$MANIFEST.asc" \
    "$MANIFEST" || {
      echo "ERROR: manifest signature self-verification failed." >&2
      exit 14
    }

  for sig in "$OUT_DIR"/*.iso.asc; do
    iso="${sig%.asc}"

    gpg \
      --batch \
      --verify \
      "$sig" \
      "$iso" || {
        echo "ERROR: ISO signature self-verification failed: $iso" >&2
        exit 15
      }
  done
fi

cat "$MANIFEST"
