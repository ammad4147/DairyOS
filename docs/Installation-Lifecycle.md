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

The data root contains:

- `storage/` — JSON-backed operational state;
- `config.json` — farm configuration managed by the lifecycle boundary;
- `logs/` — application logs;
- `backups/` — lifecycle backup sets;
- `lifecycle.json` — installation and upgrade manifest.

The PostgreSQL database remains outside the installation directory. Database backups use the standard PostgreSQL custom dump format through `pg_dump`; restore uses `pg_restore`.

## Installation

On Windows use `scripts/install/Install-DairyOS.ps1`. The script creates a dedicated virtual environment, installs DairyOS from the supplied source tree, creates the managed data root, writes the lifecycle manifest and validates the installation.

For an existing installation, use `-Upgrade`. A data backup is created before the change and the runtime directory is snapshotted so a failed upgrade can restore both the data state and the previous runtime files.

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

The Windows uninstaller performs a pre-purge backup by default, then removes the data root. The runtime is removed only after the lifecycle data operation succeeds.

Never treat a filesystem-level deletion of the runtime directory as equivalent to a data purge. Farm data lives outside the runtime installation boundary by design.
