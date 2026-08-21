from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
OS = ROOT / "os"


def read(path: str) -> str:
    return (OS / path).read_text(encoding="utf-8")


def test_os_manifest_targets_debian_trixie_amd64_and_safe_installer_mode():
    manifest = yaml.safe_load(read("manifest.yaml"))
    assert manifest["target"]["distribution"] == "debian"
    assert manifest["target"]["release"] == "trixie"
    assert manifest["target"]["architecture"] == "amd64"
    assert set(manifest["target"]["boot_modes"]) == {"uefi", "legacy-bios"}
    assert manifest["storage"]["partition_table"] == "gpt"
    assert manifest["security"]["installer_default_mode"] == "dry-run"
    assert manifest["security"]["require_target_device"] is True
    assert manifest["security"]["require_apply_switch"] is True
    assert manifest["network"]["offline_mirror"]["security_path"] == "/debian-security"


def test_partition_manifest_preserves_efi_bios_root_log_swap_and_farm_data():
    sfdisk = read("partitioning/dairyos.sfdisk")
    assert "label: gpt" in sfdisk
    assert 'name="DairyOS EFI"' in sfdisk
    assert 'name="DairyOS BIOS Boot"' in sfdisk
    assert 'name="DairyOS Root"' in sfdisk
    assert 'name="DairyOS Logs"' in sfdisk
    assert 'name="DairyOS Swap"' in sfdisk
    assert 'name="DairyOS Farm Data"' in sfdisk
    assert "21686148-6449-6E6F-744E-656564454649" in sfdisk
    assert "U32-EFI" in sfdisk
    assert "U82-Swap" in sfdisk


def test_release_and_installer_use_the_manifest_target_release():
    manifest = yaml.safe_load(read("manifest.yaml"))
    release = manifest["target"]["release"]
    build = read("build/build-iso.sh")
    installer = read("installer/install.sh")
    mirror = read("pxe/mirror/sync-debian.sh")
    assert f'DIST="{release}"' in build
    assert f"debootstrap --arch=amd64 {release}" in installer
    assert f'DIST="{release}"' in mirror


def test_installer_is_fail_closed_and_has_explicit_disk_apply_gate():
    installer = read("installer/install.sh")
    assert 'MODE="dry-run"' in installer
    assert '[[ -b "$TARGET_DEVICE" ]]' in installer
    assert "--apply" in installer
    assert 'MODE="apply"' in installer
    assert "wipefs -a \"$TARGET_DEVICE\"" in installer
    assert 'sfdisk "$TARGET_DEVICE"' in installer
    assert "grub-install --target=x86_64-efi" in installer
    assert "grub-install --target=i386-pc" in installer
    assert 'DEBIAN_MIRROR="file:///srv/dairyos-debian"' in installer
    assert "validate_mirror" in installer
    assert 'BIOS_PART="${TARGET_DEVICE}p2"' in installer
    assert 'DATA_PART="${TARGET_DEVICE}p6"' in installer
    assert 'PARTITIONING_STARTED=true' in installer
    assert 'The target disk is NOT automatically randomized or wiped.' in installer
    assert 'write_recovery_state "failed"' in installer
    assert "touch \"$MOUNT_ROOT/.install-in-progress\"" in installer
    assert "touch \"$committed\"" in installer


def test_boot_and_pxe_contracts_exist():
    grub = read("boot/grub/grub.cfg")
    pxe_grub = read("pxe/grub.cfg")
    pxe_ipxe = read("pxe/ipxe/dairyos.ipxe")
    dnsmasq = read("pxe/dnsmasq.conf")

    assert "menuentry 'DairyOS'" in grub
    assert "menuentry 'DairyOS Recovery'" in grub
    assert "search --no-floppy --label" in grub
    assert "root=LABEL=DAIRYOS-ROOT" in grub
    assert "linux /boot/vmlinuz" in grub

    assert "preseed/url=" in pxe_grub
    assert "initrd" in pxe_grub
    assert "#!ipxe" in pxe_ipxe
    assert "boot" in pxe_ipxe
    assert "enable-tftp" in dnsmasq
    assert "dhcp-boot=tag:efi64,grubx64.efi" in dnsmasq


def test_artifact_integrity_and_first_boot_assets_exist():
    for relative in (
        "build/build-iso.sh",
        "build/stage-app.sh",
        "build/release-manifest.sh",
        "installer/rollback.sh",
        "installer/teardown-purge.sh",
        "installer/preseed/dairyos.seed",
        "installer/hooks/firstboot.sh",
        "installer/hooks/validate.sh",
        "services/dairyos.service",
        "services/dairyos-firstboot.service",
        "pxe/mirror/sync-debian.sh",
        "pxe/mirror/nginx-dairyos.conf",
    ):
        assert (OS / relative).is_file(), relative

    release_builder = read("build/release-manifest.sh")
    assert "sha256sum" in release_builder
    assert "gpg" in release_builder
    assert "DAIRYOS_SIGNING_KEY" in release_builder
    assert 'DAIRYOS_ALLOW_UNSIGNED="false"' in release_builder
    assert 'exit 12' in release_builder


def test_offline_build_stages_complete_application_wheelhouse():
    stage = read("build/stage-app.sh")
    firstboot = read("installer/hooks/firstboot.sh")
    build = read("build/build-iso.sh")

    assert "pip wheel --wheel-dir" in stage
    assert "wheelhouse" in stage
    assert "--no-index" in firstboot
    assert "--find-links \"$WHEELHOUSE\"" in firstboot
    assert "pip install --no-index" in firstboot
    assert '"$OS_ROOT/build/stage-app.sh"' in build
    assert "app-stage/wheelhouse" in build
    assert "release-manifest.sh" in build


def test_bare_metal_first_boot_provisions_database_and_secrets():
    firstboot = read("installer/hooks/firstboot.sh")
    service = read("services/dairyos.service")
    assert "systemctl start postgresql" in firstboot
    assert "CREATE ROLE dairyos LOGIN PASSWORD" in firstboot
    assert "createdb -O dairyos dairyos" in firstboot
    assert "DAIRYOS_DB_HOST=127.0.0.1" in firstboot
    assert "DAIRYOS_DB_USER=dairyos" in firstboot
    assert "DAIRYOS_DB_PASSWORD=$DB_PASSWORD" in firstboot
    assert "DAIRYOS_AUTH_SECRET=$AUTH_SECRET" in firstboot
    assert "EnvironmentFile=-/etc/dairyos/dairyos.env" in service
    assert "/var/log/dairyos" in service


def test_air_gapped_mirror_contract_is_local_lan_only_by_default():
    manifest = yaml.safe_load(read("manifest.yaml"))
    preseed = read("installer/preseed/dairyos.seed")
    installer = read("installer/install.sh")
    sync_script = read("pxe/mirror/sync-debian.sh")
    nginx = read("pxe/mirror/nginx-dairyos.conf")

    assert manifest["network"]["wan_required_for_first_boot"] is False
    assert manifest["network"]["offline_mirror"]["host"] == "192.168.50.1"
    assert "apt-setup/mirror/http/hostname string 192.168.50.1" in preseed
    assert "apt-setup/mirror/http/directory string /debian" in preseed
    assert "apt-setup/security_host string 192.168.50.1" in preseed
    assert "method{ biosgrub }" in preseed
    assert "file:///srv/dairyos-debian" in installer
    assert "debmirror" in sync_script
    assert "debian-security" in sync_script
    assert "/srv" in nginx
    assert "location /debian/" in nginx
    assert "location /debian-security/" in nginx


def test_systemd_service_uses_persistent_farm_data_path():
    service = read("services/dairyos.service")
    firstboot_service = read("services/dairyos-firstboot.service")
    assert "After=network-online.target postgresql.service" in service
    assert "Environment=DAIRYOS_DATA_DIR=/var/lib/dairyos" in service
    assert "ReadWritePaths=/var/lib/dairyos" in service
    assert "Requires=postgresql.service" in firstboot_service
    assert "ConditionPathExists=/opt/dairyos-os/installer/firstboot.sh" in firstboot_service
    assert "ConditionPathExists=!/var/lib/dairyos/.firstboot-complete" in firstboot_service


def test_teardown_handles_nvme_and_mmc_partition_naming_and_unmounts_first():
    teardown = read("installer/teardown-purge.sh")
    assert 'TARGET_DEVICE##*/' in teardown
    assert 'DATA_PART="${TARGET_DEVICE}p6"' in teardown
    assert 'findmnt -rn -S "$TARGET_DEVICE"' in teardown
    assert 'umount -R "$mountpoint"' in teardown
    assert 'wipefs -a "$TARGET_DEVICE"' in teardown
    assert 'sgdisk --zap-all "$TARGET_DEVICE"' in teardown
