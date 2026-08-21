#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS="$ROOT/AUDIT/results"
mkdir -p "$RESULTS"

exec > >(tee "$RESULTS/host-regression.txt") 2>&1

cd "$ROOT"

echo "=== DairyOS current-main host regression ==="
echo "Repository: $ROOT"
echo "Commit: $(git rev-parse HEAD)"

test -f pyproject.toml
command -v python3 >/dev/null
test -d tests

printf '\n=== Python compileall ===\n'
python3 -m compileall -q src

printf '\n=== Full pytest regression ===\n'
PYTHONPATH=src pytest -q

printf '\n=== OS artifact contract regression ===\n'
PYTHONPATH=src pytest -q tests/platform/test_os_distribution_artifacts.py

printf '\nPASS: current-main host regression completed.\n'
