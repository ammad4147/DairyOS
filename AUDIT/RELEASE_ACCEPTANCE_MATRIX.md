# DairyOS Windows Installer Release Acceptance Matrix

Repository: `ammad4147/DairyOS`
Authoritative branch: `main`
Supported deployment target: **Windows application installer only**

This matrix is the sole release gate for the supported DairyOS deployment product.

| Gate | Evidence mechanism | Status rule |
|---|---|---|
| Repository reconciliation | Git branch/status/HEAD verification | Must pass |
| Full backend regression | `python -m pytest -q` | Must pass |
| Frontend typecheck/build | `npm run typecheck` and `npm run build` | Must pass |
| Fresh Windows installation | Clean Windows target + installer | Must pass |
| Zero-state validation | New installation contains no farm/demo/test data | Must pass |
| Runtime startup | Installed application starts without developer commands | Must pass |
| Health/readiness | `/health` and `/readiness` or equivalent runtime checks | Must pass |
| PostgreSQL initialization/migration | Fresh supported database initialization | Must pass |
| Upgrade preservation | Upgrade populated installation without farm-data loss | Must pass |
| Uninstall/reinstall preservation | Application removal/reinstall preserves governed farm data | Must pass |
| Windows reboot recovery | Reboot target and verify automatic healthy runtime | Must pass |
| Installer artifact integrity | Installer hash/version/build evidence | Must pass |
| Production contamination check | No fixtures/demo/test data in installed runtime | Must pass |
| Backup/restore | Restore production data into clean supported environment | Must pass |
| Windows hardware compatibility | Supported Windows hardware/runtime matrix | Must pass |

## Interpretation

A successful automated regression run establishes source-level correctness only. Windows deployment acceptance additionally requires evidence from the actual installer, a clean installation, a populated installation upgrade, uninstall/reinstall preservation, reboot recovery, zero-state verification, and backup/restore testing.
