#!/usr/bin/env bash
set -Eeuo pipefail

errors=0
fail() { echo "FAIL: $*" >&2; errors=$((errors + 1)); }
pass() { echo "PASS: $*"; }

[[ "$(id -u)" -eq 0 ]] || { echo "Run as root." >&2; exit 20; }

for path in /boot/efi /var/log /var/lib/dairyos /etc/systemd/system/dairyos.service /etc/systemd/system/dairyos-firstboot.service; do
  if [[ -e "$path" ]]; then pass "$path exists"; else fail "$path missing"; fi
done

if command -v findmnt >/dev/null 2>&1; then
  findmnt /boot/efi >/dev/null 2>&1 && pass "/boot/efi mounted" || fail "/boot/efi not mounted"
  findmnt /var/log >/dev/null 2>&1 && pass "/var/log mounted" || fail "/var/log not mounted"
  findmnt /var/lib/dairyos >/dev/null 2>&1 && pass "/var/lib/dairyos mounted" || fail "/var/lib/dairyos not mounted"
fi

systemctl is-enabled dairyos.service >/dev/null 2>&1 && pass "dairyos.service enabled" || fail "dairyos.service not enabled"
systemctl is-enabled dairyos-firstboot.service >/dev/null 2>&1 && pass "firstboot service enabled" || fail "firstboot service not enabled"

if [[ -f /etc/fstab ]]; then
  grep -q 'DAIRYOS-ROOT' /etc/fstab && pass 'root filesystem in fstab' || fail 'root filesystem absent from fstab'
  grep -q 'DAIRYOS-DATA' /etc/fstab && pass 'farm data filesystem in fstab' || fail 'farm data filesystem absent from fstab'
else
  fail '/etc/fstab missing'
fi

if [[ "$errors" -gt 0 ]]; then
  echo "Validation failed with $errors error(s)." >&2
  exit 2
fi

echo "DairyOS installed-system validation passed."