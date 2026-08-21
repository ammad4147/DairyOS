from __future__ import annotations
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[2]
OS = ROOT / "os"
def read(path: str) -> str: return (OS / path).read_text(encoding="utf-8")

def test_os_manifest_targets_debian_trixie_amd64_and_safe_installer_mode():
    manifest = yaml.safe_load(read("manifest.yaml")); assert manifest["target"]["distribution"] == "debian"; assert manifest["target"]["release"] == "trixie"; assert manifest["target"]["architecture"] == "amd64"; assert set(manifest["target"]["boot_modes"]) == {"uefi", "legacy-bios"}; assert manifest["storage"]["partition_table"] == "gpt"; assert manifest["security"]["installer_default_mode"] == "dry-run"; assert manifest["security"]["require_target_device"] is True; assert manifest["security"]["require_apply_switch"] is True; assert manifest["network"]["offline_mirror"]["security_path"] == "/debian-security"

def test_partition_manifest_preserves_efi_bios_root_log_swap_and_farm_data():
    sfdisk=read("partitioning/dairyos.sfdisk");
    for x in ('label: gpt','name="DairyOS EFI"','name="DairyOS BIOS Boot"','name="DairyOS Root"','name="DairyOS Logs"','name="DairyOS Swap"','name="DairyOS Farm Data"','21686148-6449-6E6F-744E-656564454649','U32-EFI','U82-Swap'): assert x in sfdisk

def test_release_and_installer_use_manifest_release():
    m=yaml.safe_load(read("manifest.yaml")); r=m["target"]["release"]; assert f'DIST="{r}"' in read("build/build-iso.sh"); assert f"debootstrap --arch=amd64 {r}" in read("installer/install.sh"); assert f'DIST="{r}"' in read("pxe/mirror/sync-debian.sh")

def test_installer_fail_closed():
    x=read("installer/install.sh");
    for s in ('MODE="dry-run"','[[ -b "$TARGET_DEVICE" ]]','--apply','MODE="apply"','wipefs -a "$TARGET_DEVICE"','sfdisk "$TARGET_DEVICE"','grub-install --target=x86_64-efi','grub-install --target=i386-pc','DEBIAN_MIRROR="file:///srv/dairyos-debian"','validate_mirror','BIOS_PART="${TARGET_DEVICE}p2"','DATA_PART="${TARGET_DEVICE}p6"','PARTITIONING_STARTED=true','write_recovery_state "failed"','.install-in-progress'): assert s in x
    assert 'dd if=/dev/urandom' not in x

def test_boot_and_pxe_contracts_exist():
    grub=read("boot/grub/grub.cfg"); pg=read("pxe/grub.cfg"); ip=read("pxe/ipxe/dairyos.ipxe"); dns=read("pxe/dnsmasq.conf")
    for s in ("menuentry 'DairyOS'","menuentry 'DairyOS Recovery'","search --no-floppy --label","root=LABEL=DAIRYOS-ROOT","linux /boot/vmlinuz"): assert s in grub
    assert "preseed/url=" in pg; assert "initrd" in pg; assert "#!ipxe" in ip; assert "boot" in ip; assert "enable-tftp" in dns; assert "dhcp-boot=tag:efi64,grubx64.efi" in dns

def test_artifacts_and_release_signing_contract():
    for p in ("build/build-iso.sh","build/stage-app.sh","build/release-manifest.sh","installer/rollback.sh","installer/teardown-purge.sh","installer/preseed/dairyos.seed","installer/hooks/firstboot.sh","installer/hooks/validate.sh","services/dairyos.service","services/dairyos-firstboot.service","pxe/mirror/sync-debian.sh","pxe/mirror/nginx-dairyos.conf"): assert (OS/p).is_file(), p
    x=read("build/release-manifest.sh"); assert "sha256sum" in x; assert "gpg" in x; assert "DAIRYOS_SIGNING_KEY" in x; assert 'DAIRYOS_ALLOW_UNSIGNED="false"' in x; assert 'iso.asc' in x

def test_offline_build_stages_wheelhouse():
    stage=read("build/stage-app.sh"); fb=read("installer/hooks/firstboot.sh"); b=read("build/build-iso.sh"); assert "pip wheel --wheel-dir" in stage; assert "wheelhouse" in stage; assert "--no-index" in fb; assert "--find-links \"$WHEELHOUSE\"" in fb; assert "pip install --no-index" in fb; assert '"$OS_ROOT/build/stage-app.sh"' in b; assert "app-stage/wheelhouse" in b; assert "release-manifest.sh" in b

def test_bare_metal_firstboot():
    fb=read("installer/hooks/firstboot.sh"); s=read("services/dairyos.service");
    for x in ("systemctl start postgresql","CREATE ROLE dairyos LOGIN PASSWORD","createdb -O dairyos dairyos","DAIRYOS_DB_HOST=127.0.0.1","DAIRYOS_DB_USER=dairyos","DAIRYOS_DB_PASSWORD=$DB_PASSWORD","DAIRYOS_AUTH_SECRET=$AUTH_SECRET","EnvironmentFile=-/etc/dairyos/dairyos.env","/var/log/dairyos"): assert x in fb+s

def test_airgap_contract():
    m=yaml.safe_load(read("manifest.yaml")); p=read("installer/preseed/dairyos.seed"); i=read("installer/install.sh"); sy=read("pxe/mirror/sync-debian.sh"); n=read("pxe/mirror/nginx-dairyos.conf"); assert m["network"]["wan_required_for_first_boot"] is False; assert m["network"]["offline_mirror"]["host"] == "192.168.50.1"; assert "apt-setup/security_host string 192.168.50.1" in p; assert "file:///srv/dairyos-debian" in i; assert "debmirror" in sy; assert "debian-security" in sy; assert "location /debian-security/" in n

def test_systemd_persistence():
    s=read("services/dairyos.service"); f=read("services/dairyos-firstboot.service"); assert "After=network-online.target postgresql.service" in s; assert "Environment=DAIRYOS_DATA_DIR=/var/lib/dairyos" in s; assert "ReadWritePaths=/var/lib/dairyos" in s; assert "Requires=postgresql.service" in f; assert "ConditionPathExists=!/var/lib/dairyos/.firstboot-complete" in f

def test_teardown_safe():
    x=read("installer/teardown-purge.sh"); assert 'TARGET_DEVICE##*/' in x; assert 'SWAP_PART="${TARGET_DEVICE}p5"' in x; assert 'DATA_PART="${TARGET_DEVICE}p6"' in x; assert 'swapoff -a' not in x; assert 'findmnt -rn -S "$TARGET_DEVICE"' in x; assert 'umount -R "$mountpoint"' in x; assert 'wipefs -a "$TARGET_DEVICE"' in x; assert 'sgdisk --zap-all "$TARGET_DEVICE"' in x

def test_release_acceptance_harness_exists():
    for p in ("AUDIT/RELEASE_ACCEPTANCE_MATRIX.md","AUDIT/verify-release.sh","AUDIT/run-host-regression.sh","AUDIT/run-disaster-simulations.sh"): assert (ROOT/p).is_file(), p
