# DairyOS Administrative Tool

The DairyOS Administrative Tool is a separate operator surface for privileged lifecycle, recovery, maintenance, and destructive operations. It is intentionally outside the normal DairyOS operational UI.

## Operational boundary

The main DairyOS application remains the nine-tab operational application. It does not provide a password gate for lifecycle administration and must not acquire an administrative tab merely to expose maintenance functions.

The supported privileged boundary is the standalone `dairyos-admin` / `dairyos-admin-cli` tool. It delegates lifecycle work to the canonical lifecycle subsystem rather than implementing a competing lifecycle manager.

## Supported operations

- Validate installation and database health
- Create verified backups
- Restore verified snapshots
- Roll back to a verified snapshot
- Reset operational farm/application data
- Permanent purge with explicit confirmation and external recovery backup
- Uninstall while retaining data, or purge when explicitly confirmed

## Reset safety contract

Reset requires the exact confirmation text `RESET DAIRYOS DATA`, a healthy configured PostgreSQL database, and the normal DairyOS runtime must be stopped.

Before mutation, the Admin Tool creates a PostgreSQL/filesystem snapshot, records the database dump SHA-256, copies the recovery artifact outside the data root, and verifies the artifact. The reset coordinator then atomically deactivates deployment and truncates non-preserved operational tables. Zero-state is verified after the transaction. If the operation fails, the pre-reset snapshot is used for recovery.

Preserved configuration/reference tables are explicitly defined by the lifecycle reset coordinator. This list must be reviewed whenever new persistent tables are introduced.

## Windows

Use `scripts/Start-DairyOS-Admin.ps1` for the source-installed administrative surface. `scripts/Build-DairyOS-Admin.ps1` builds a separate `DairyOS-Admin` executable with PyInstaller using `packaging/dairyos_admin.spec`.

The Windows build is a separate executable and is not the DairyOS operational desktop executable.
