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


def test_partition_manifest_preserves_separate_log_and_farm_data_partitions():
    sfdisk = read("partitioning/dairyos.sfdisk")
    assert "label: gpt" in sfdisk
    assert 'name="DairyOS EFI"' in sfdisk
    assert 'name="DairyOS Root"' in sfdisk
    assert 'name="DairyOS Logs"' in sfdisk
    assert 'name="DairyOS Farm Data"' in sfdisk
    assert "U32-EFI" in sfdisk
    assert "U82-Swap" in sfdisk


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
    assert "touch \"$MOUNT_ROOT/.install-in-progress\"" in installer
    assert "touch \"$committed\"" in installer


def test_boot_and_pxe_contracts_exist():
    grub = read("boot/grub/grub.cfg")
    pxe_grub = read("pxe/grub.cfg")
    pxe_ipxe = read("pxe/ipxe/dairyos.ipxe")
    dnsmasq = read("pxe/dnsmasq.conf")

    assert "menuentry 'DairyOS'" in grub
    assert "menuentry 'DairyOS Recovery'" in grub
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
        "build/release-manifest.sh",
        "installer/rollback.sh",
        "installer/preseed/dairyos.seed",
        "installer/hooks/firstboot.sh",
        "installer/hooks/validate.sh",
        "services/dairyos.service",
        "services/dairyos-firstboot.service",
    ):
        assert (OS / relative).is_file(), relative

    release_builder = read("build/release-manifest.sh")
    assert "sha256sum" in release_builder
    assert "gpg" in release_builder
    assert "DAIRYOS_SIGNING_KEY" in release_builder


def test_systemd_service_uses_persistent_farm_data_path():
    service = read("services/dairyos.service")
    firstboot = read("services/dairyos-firstboot.service")
    assert "After=network-online.target postgresql.service" in service
    assert "Environment=DAIRYOS_DATA_DIR=/var/lib/dairyos" in service
    assert "ReadWritePaths=/var/lib/dairyos" in service
    assert "ConditionPathExists=/opt/dairyos-os/installer/firstboot.sh" in firstboot
