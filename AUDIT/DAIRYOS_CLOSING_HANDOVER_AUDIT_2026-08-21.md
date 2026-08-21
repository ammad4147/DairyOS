# DairyOS Closing & Handover Audit — 2026-08-21

## Authority

Repository: `ammad4147/DairyOS`

Authoritative remote branch: `main`

Current audited tip: `de18f0d47ce7a399550f2151a3ba53872c5159e3`

GitHub currently exposes one remote branch: `main`.

## Phase 0 — Artifact inventory

**Gate: PASS at source level.**

The tree contains the Debian trixie amd64 manifest, GPT partition definition, UEFI/legacy-BIOS GRUB configuration, installer, rollback/purge, unattended preseed, first-boot services, LAN Debian/security mirror tooling, PXE/iPXE configuration, ISO build, application staging, release signing, and OS contract tests.

A formal acceptance matrix, host regression harness, disaster-safety harness, and release verifier are now also present under `AUDIT/`.

## Phase 1 — Lifecycle/code wiring

The following defects were corrected during the closing work:

- Debian release mismatch between manifest and build/installer: aligned on trixie.
- GPT legacy-BIOS boot gap: added BIOS boot partition and matching preseed.
- Offline security mirror leakage: security archive is routed through the LAN mirror.
- Destructive installer failure trap: replaced with recorded recovery state and non-destructive failure handling.
- Purge NVMe/MMC partition addressing: corrected for p5 swap and p6 data.
- Purge global `swapoff -a`: removed; only target swap is disabled.
- Release signing: ISO and SHA256 manifest detached signatures are generated and self-verified when a signing key is supplied; unsigned output requires explicit development override.
- Release ISO builder: now fails if a signed release ISO is not produced.
- Closing acceptance harness: added reproducible regression, disaster-contract, release-verification, checksum, signature, and ISO inspection tooling.

## Phase 2 — Hardware/veterinary environment

**Gate: OPEN — execution required.**

Static configuration exists for farm peripherals, but source inspection cannot prove physical RFID, scale-meter, parlor PLC/gateway, USB/serial, storage, or power-recovery compatibility. These require designated hardware execution and evidence capture.

## Phase 3 — Disaster simulations

**Gate: OPEN — execution required.**

The repository now has static safety contracts for all three scenarios, but those are not substitutes for real tests:

- Scenario A: actual interruption during partition/filesystem writing — not physically proven.
- Scenario B: WAN physically disconnected during PXE/installation — not physically proven.
- Scenario C: real teardown including EFI NVRAM and partition-table verification — not physically proven.

The purge implementation now explicitly refuses a target containing the running host's root/boot mounts and does not disable unrelated host swap.

## Regression and actual ISO build

A GitHub Actions release workflow is now part of `main` and is triggered on pushes to `main` and manually. It:

1. enforces the one-branch policy;
2. installs Live-Build, Debian bootstrap, GRUB, QEMU/OVMF and test dependencies;
3. runs the current-main Python regression suite;
4. runs disaster-safety contracts;
5. creates a short-lived CI GPG signing key;
6. builds the **actual `dairyos-trixie-amd64.iso`** using `os/build/build-iso.sh`;
7. verifies SHA-256 and detached signatures;
8. inspects ISO El Torito/system-area metadata;
9. boots the ISO in a disposable UEFI QEMU VM;
10. generates a GitHub build-provenance attestation; and
11. uploads the ISO and evidence bundle.

The workflow is intended to provide the missing executable ISO-build evidence at the end of the audit. The available connector currently reports no workflow run for the audited commit, so a successful build cannot yet be claimed from this session.

## Local reconciliation

**BLOCKING — NOT VERIFIED.**

The Windows path `D:\DairyOS` is outside this execution environment. The required final local operation is to fetch `origin/main`, inspect local divergence, switch to `main`, hard-reset to `origin/main`, remove untracked build artifacts if safe, and verify an empty working tree. The local `HEAD` must equal the current remote `main` tip exactly.

## Release disposition

**NOT ACCEPTED FOR RELEASE YET.**

Source defects found during the closing audit have been addressed and the actual-build automation is now in place. Formal acceptance still requires successful execution evidence for the current `main`, including the actual ISO build, UEFI/legacy-BIOS boot, full regression, air-gapped deployment, power-loss recovery, physical teardown/NVRAM cleanup, farm hardware matrix, and final `D:\DairyOS` reconciliation.
