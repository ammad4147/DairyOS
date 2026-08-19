# DairyOS OS Handover - Phase 1 Progress

Date: 2026-08-19
Branch: audit/os-handover-2026-08-19
Base: main at aeb5cc98ac79fbdb30c77050202242cd34bca299

## Phase 0 remediation status

The four Phase 0 blockers have corresponding implementation artifacts on this branch:

| Blocker | Implementation |
|---|---|
| Bootloader / EFI | `os/boot/grub/grub.cfg`, installer `grub-install` UEFI + BIOS paths |
| Installer / provisioning | `os/installer/install.sh`, preseed, firstboot and validation hooks |
| Partitioning | `os/partitioning/dairyos.sfdisk`, installer partition transaction |
| PXE / network boot | `os/pxe/dnsmasq.conf`, UEFI GRUB PXE, iPXE, local Debian mirror |

## Distribution baseline

- Debian 13 (trixie), amd64
- UEFI and legacy BIOS
- GPT storage
- Dedicated EFI, root, `/var/log`, swap and `/var/lib/dairyos` filesystems
- GRUB recovery menu
- systemd-managed PostgreSQL and DairyOS services
- first-boot local credential/bootstrap generation
- offline wheelhouse for application installation
- local farm Debian package mirror for air-gapped installation

Debian 13.6 is the point-release baseline recorded by this audit. Debian publishes installer images and SHA256 verification files for Debian 13.6, and the official amd64 netboot tree provides `grubx64.efi`, `linux` and `initrd.gz` assets.

## Safety properties

The bare-metal installer is dry-run by default and requires both `--target-device` and `--apply` before destructive disk operations. It validates device class and a 32 GiB minimum size and places an installation lock before writing the target.

Normal application teardown keeps `/var/lib/dairyos`. Destructive purge remains explicit and confirmation-gated.

## Acceptance status

**NOT ACCEPTED.** Source/build contracts are implemented, but final handover still requires execution evidence for:

1. ISO build and SHA256/signature verification.
2. UEFI boot and legacy BIOS boot in virtual machines.
3. Installation to disposable virtual disks using the actual installer.
4. Air-gapped PXE installation using a local Debian mirror.
5. Power interruption during partitioning and recovery/rollback.
6. Physical edge-node installation and hardware/peripheral compatibility.
7. Keep-data uninstall, bootloader cleanup and purge on a disposable target.

These gates cannot be inferred from static source inspection.