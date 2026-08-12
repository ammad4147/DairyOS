# DR-001 — DairyOS Backup & Disaster Recovery

## Scope

DairyOS uses PostgreSQL as the authoritative persistence boundary for operational records. Disaster recovery therefore requires a real PostgreSQL backup, checksum verification, and a tested restore path.

## Backup

With the DairyOS environment configured, create a backup with:

```powershell
python -m dairyos.platform.backup backup D:\DairyOS-backups\<timestamp>
```

The backup directory contains:

- `dairyos.dump` — PostgreSQL custom-format logical backup
- `manifest.json` — database metadata, size and SHA-256 checksum

The backup command fails if `pg_dump` is unavailable, the dump command fails, or an empty dump is produced.

## Restore

Restore only from a directory containing a valid manifest and matching checksum:

```powershell
python -m dairyos.platform.backup restore D:\DairyOS-backups\<timestamp>
```

DairyOS refuses to restore when the manifest is missing, the payload is missing, or the SHA-256 checksum does not match. PostgreSQL `pg_restore` is invoked with `--clean`, `--if-exists`, and `--no-owner`.

## Credentials

The backup tooling uses the same `DAIRYOS_DATABASE_URL` / `DAIRYOS_DB_*` configuration as the application. Passwords are supplied to PostgreSQL through `PGPASSWORD` and are not written to the manifest.

## Operational acceptance test

A deployment is not considered disaster-recovery ready merely because a backup file exists. The operator must periodically perform a restore into an isolated PostgreSQL database and verify:

1. backup creation succeeds;
2. manifest checksum matches the payload;
3. restore succeeds;
4. schema is available;
5. Animal Register records survive;
6. milk, health, treatment/withdrawal, breeding, feed and finance records survive;
7. operational events/state survive;
8. the application can reconnect and operate against the restored database.

The automated tests in `tests/platform/test_backup.py` cover command failure handling, manifest generation, checksum verification, and safe restore invocation. A production restore drill remains an operational deployment exercise and must not be represented as completed until it has actually been performed against an isolated recovery database.
