# DairyOS Installation, Upgrade, Recovery and Uninstallation Lifecycle

DairyOS separates runtime files from farm data. Runtime files may be replaced or removed; farm data is retained unless the operator explicitly chooses permanent purge.

## Lifecycle

```text
Install
  -> Validate
  -> Backup
  -> Upgrade
  -> Validate
  -> Rollback on failure
  -> Uninstall
       -> Keep Data
       -> Purge Data (explicit confirmation)
```

## Data boundary

The managed farm-data root is controlled by `DAIRYOS_DATA_DIR` and is resolved by `dairyos.platform.paths`. On Windows a conventional default is under `%LOCALAPPDATA%\DairyOS`; the supported production installer sets a farm-wide root under `%PROGRAMDATA%\DairyOS`.

The data root contains operational state, configuration, logs and lifecycle metadata. PostgreSQL remains outside the runtime installation directory.

Lifecycle backups are treated differently from live farm data: normal lifecycle snapshots are written under the managed backup area, while a destructive purge first makes a second copy under the sibling `DairyOS-PurgeBackups` directory so the recovery artifact survives deletion of the live data root.

## Installation

On Windows use `scripts/install/Install-DairyOS.ps1`. The script creates a dedicated virtual environment, installs DairyOS from the supplied source tree, creates the managed data root, writes the lifecycle manifest and validates the installation.

For an existing installation, use `-Upgrade`. A data backup is created before the change and the runtime directory is snapshotted so a failed upgrade can restore both the data state and the previous runtime files.

### New empty farm versus existing farm data

The Windows installer treats **Create a separate empty farm** as a
non-destructive provisioning operation. When an existing farm is detected,
the installer allocates a new sibling data root and points the new installation
at that root. It never clears, replaces, scans arbitrary drives for, or
deletes the existing farm database, logs, storage, or backups. The previous
root remains available for a later Keep or explicitly selected Restore action.

The installer only looks for recovery points in the active DairyOS backup
directory and explicitly configured recovery/mirror roots. A backup-only
directory is not treated as proof that an active farm should be reused.

The terms **new empty farm** and **clean install** must therefore never be
implemented as a reset. Permanent removal is a separate, explicitly named
purge operation and is not part of installation.

## Validation

The lifecycle validator checks:

- Python 3.12 or newer;
- required data directories;
- data-directory writability;
- installation-root presence;
- lifecycle manifest presence;
- PostgreSQL connectivity when a database URL is configured.

The operational test suite remains the authoritative application behavior gate.

## Backup and rollback

`dairyos-lifecycle backup` produces a timestamped backup set containing:

- copied configuration, JSON state and logs;
- file sizes and SHA-256 digests;
- a PostgreSQL `database.dump` when a PostgreSQL URL is supplied;
- backup metadata and application/runtime identifiers.

`dairyos-lifecycle rollback <backup>` restores the data snapshot and, when present, the PostgreSQL database dump.

## Uninstallation

`KeepData` removes the runtime while retaining the farm data root for a future reinstall.

`PurgeData` requires the exact confirmation text:

```text
PURGE DAIRYOS DATA
```

The Windows uninstaller performs a pre-purge backup by default. The runtime is removed only after the lifecycle data operation succeeds. The purge workflow makes the surviving backup copy outside the data root before deleting the live data root.

Never treat a filesystem-level deletion of the runtime directory as equivalent to a data purge. Farm data lives outside the runtime installation boundary by design.
