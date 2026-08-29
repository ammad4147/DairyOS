# DairyOS Administration Tool

The administrative tool is a separate operator surface for privileged lifecycle and recovery operations. It is not part of the nine-tab DairyOS operational UI.

## Boundary

The operational application does not provide an administrative password gate or a destructive reset implementation. Privileged actions are performed from this standalone tool and delegated to the canonical `dairyos.lifecycle` services.

## Entry points

- `dairyos-admin` starts the standalone local administration UI.
- `dairyos-admin-cli` provides explicit operator automation.
- `scripts/Start-DairyOS-Admin.ps1` is the Windows development/operator launcher.

## Administrative operations

- Validate installation and database health
- Create verified backup
- Restore a verified snapshot
- Roll back to a verified snapshot
- Reset operational farm data
- Permanently purge the data root
- Uninstall while optionally retaining data

## Reset safety boundary

Reset is not implemented through `/settings/reset`. The standalone Admin Tool:

1. requires the exact operation-specific confirmation token;
2. requires a healthy configured PostgreSQL database;
3. fails closed if the normal DairyOS backend is still listening;
4. creates a lifecycle pre-reset backup;
5. records the PostgreSQL dump SHA-256 in the backup manifest;
6. copies the recovery artifact outside the DairyOS data root;
7. verifies filesystem and database-backup checksums;
8. records reset intent externally;
9. deactivates the persisted deployment gate;
10. truncates every discovered non-preserved operational table with identity reset and cascade;
11. verifies the resulting zero-state across the complete operational table inventory;
12. records the reset result externally; and
13. restores the pre-reset lifecycle snapshot if mutation or verification fails.

## Destructive-operation rule

Confirmation tokens are operation guards, not an authentication system. Authorization belongs to the external administrative execution context.

Permanent purge continues to use the existing external-backup boundary so the recovery artifact survives data-root deletion.
