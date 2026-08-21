#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS="$ROOT/AUDIT/results"
mkdir -p "$RESULTS"

exec > >(tee "$RESULTS/disaster-simulations.txt") 2>&1

cd "$ROOT"

echo "=== DairyOS disaster safety contracts ==="
echo "Repository: $ROOT"
echo "Commit: $(git rev-parse HEAD)"

command -v python3 >/dev/null
command -v pytest >/dev/null

echo
printf '%s\n' '=== Scenario A: power-cut recovery contract ==='
grep -Fq 'PARTITIONING_STARTED=true' os/installer/install.sh
grep -Fq 'write_recovery_state "failed"' os/installer/install.sh
grep -Fq '.install-in-progress' os/installer/install.sh
grep -Fq 'The target disk is NOT automatically randomized or wiped.' os/installer/install.sh

echo 'PASS: installer interruption/recovery contract is present.'

echo
printf '%s\n' '=== Scenario B: air-gapped deployment contract ==='
python3 - <<'PY'
from pathlib import Path
import yaml
root = Path('.')
manifest = yaml.safe_load((root/'os/manifest.yaml').read_text())
assert manifest['network']['wan_required_for_first_boot'] is False
assert manifest['network']['offline_mirror']['host'] == '192.168.50.1'
preseed = (root/'os/installer/preseed/dairyos.seed').read_text()
installer = (root/'os/installer/install.sh').read_text()
sync = (root/'os/pxe/mirror/sync-debian.sh').read_text()
nginx = (root/'os/pxe/mirror/nginx-dairyos.conf').read_text()
assert 'apt-setup/security_host string 192.168.50.1' in preseed
assert 'file:///srv/dairyos-debian' in installer
assert 'debmirror' in sync
assert 'debian-security' in sync
assert 'location /debian-security/' in nginx
PY
echo 'PASS: offline mirror and first-boot air-gap contract is present.'

echo
echo '=== Scenario C: teardown/purge safety contract ==='
grep -Fq 'TARGET_DEVICE##*/' os/installer/teardown-purge.sh
grep -Fq 'SWAP_PART="${TARGET_DEVICE}p5"' os/installer/teardown-purge.sh
grep -Fq 'DATA_PART="${TARGET_DEVICE}p6"' os/installer/teardown-purge.sh
grep -Fq 'findmnt -rn -S "$TARGET_DEVICE"' os/installer/teardown-purge.sh
grep -Fq 'umount -R "$mountpoint"' os/installer/teardown-purge.sh
grep -Fq 'wipefs -a "$TARGET_DEVICE"' os/installer/teardown-purge.sh
grep -Fq 'sgdisk --zap-all "$TARGET_DEVICE"' os/installer/teardown-purge.sh
! grep -Fq 'swapoff -a' os/installer/teardown-purge.sh

echo 'PASS: target-scoped teardown/purge safety contract is present.'

echo
echo '=== Contract test execution ==='
PYTHONPATH=src pytest -q tests/platform/test_os_distribution_artifacts.py

echo
echo 'PASS: disaster safety contract suite completed.'
