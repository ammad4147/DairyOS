# DairyOS Appliance OS

DairyOS OS distribution baseline: Debian 13 (trixie) amd64.

Debian 13.6 is the current point release at the time of this audit. The official Debian installer provides amd64 installation media and network-boot images, with published SHA256 verification data. See the Debian 13.6 installation information and installation guide.

## Design goals

- UEFI and legacy BIOS boot through GRUB.
- GPT storage with a dedicated EFI system partition, root filesystem, log filesystem, and persistent DairyOS data filesystem.
- Offline-first application deployment from a locally staged wheel/package repository.
- First boot is deterministic and recoverable.
- Installer is fail-closed and does not touch a target disk unless `--target-device` and `--apply` are both supplied.
- Farm data is retained by default during application teardown.
- Destructive purge requires an exact confirmation token.
- PXE/iPXE assets are shipped as configuration, while the Debian netboot binaries are fetched and verified by the build host from Debian's signed distribution tree.

## Directory map

```text
os/
  boot/grub/grub.cfg                 GRUB menu contract
  build/build-iso.sh                 reproducible live ISO build entry point
  build/release-manifest.sh          SHA-256 manifest/signature helper
  config/dairyos-os.env              OS constants
  installer/install.sh               safety-gated bare-metal installer
  installer/rollback.sh              boot/data rollback helper
  installer/preseed/dairyos.seed     unattended Debian installer seed
  installer/hooks/firstboot.sh       first-boot provisioning
  installer/hooks/validate.sh        installed-system validation
  partitioning/dairyos.sfdisk        GPT partition layout
  pxe/dnsmasq.conf                   local DHCP/TFTP reference
  pxe/grub.cfg                       UEFI PXE menu
  pxe/ipxe/dairyos.ipxe              iPXE menu
  services/dairyos.service           systemd service
  services/dairyos-firstboot.service first boot unit
  manifest.yaml                      auditable target definition
```

## Safety

The installer is intended to be executed on a Linux target or from Debian Installer/recovery media. It is not a Windows disk-writing tool. On Windows, use WSL or a real Linux build/deployment host for image generation and run the installer only against a disposable target device or virtual disk first.

No OS handover acceptance is implied merely by the presence of these files. The audit requires actual image builds, boot tests, installation tests, rollback tests, and hardware/PXE execution evidence.