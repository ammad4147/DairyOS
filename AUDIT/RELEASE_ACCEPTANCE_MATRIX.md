# DairyOS Release Acceptance Matrix

Repository: `ammad4147/DairyOS`
Authoritative branch: `main`

This matrix separates source-level contracts from execution evidence. A static contract is not treated as proof of physical hardware behavior.

| Gate | Evidence mechanism | Status rule |
|---|---|---|
| Repository reconciliation | Git branch/status/HEAD verification | Must pass |
| Current-main regression | `AUDIT/run-host-regression.sh` | Must pass |
| Disaster safety contracts | `AUDIT/run-disaster-simulations.sh` | Must pass |
| Release checksum/signatures | `AUDIT/verify-release.sh` | Must pass |
| Actual ISO build | `os/build/build-iso.sh` from release workflow | Must pass |
| ISO El Torito/system-area inspection | `xorriso` release verification | Must pass |
| Disposable UEFI boot | QEMU/OVMF workflow step | Must pass |
| Build provenance | GitHub artifact attestation | Must pass |
| Physical power-loss recovery | Dedicated target hardware | Open until executed |
| Physical air-gapped PXE | Isolated PXE/LAN lab | Open until executed |
| Physical teardown/NVRAM cleanup | Dedicated target hardware | Open until executed |
| Farm hardware compatibility | RFID/scale/parlor/storage/power matrix | Open until executed |

## Interpretation

A successful CI run establishes source-level regression, actual ISO construction, cryptographic verification, ISO structure, and disposable UEFI boot evidence. It does not by itself establish physical hardware, power-loss, air-gap, NVRAM, or farm-peripheral compatibility.
