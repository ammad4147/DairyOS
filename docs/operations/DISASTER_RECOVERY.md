# DairyOS Backup & Disaster Recovery

## Scope

DairyOS operational truth lives in PostgreSQL. A deployment is not considered
recoverable until a native PostgreSQL dump has been created, inspected, and
restored successfully into a disposable target database.

## Backup

From `D:\DairyOS` with `DATABASE_URL` configured:

```powershell
python scripts\database_backup.py backup --output backups\dairyos-latest.dump
```

The utility uses `pg_dump --format=custom` and immediately verifies the dump
with `pg_restore --list`.

## Verify an existing backup

```powershell
python scripts\database_backup.py verify --input backups\dairyos-latest.dump
```

A non-empty file is not sufficient: `pg_restore --list` must successfully
enumerate its contents.

## Restore drill

Create a disposable PostgreSQL database and restore into it:

```powershell
python scripts\database_backup.py restore `
  --input backups\dairyos-latest.dump `
  --target-url "postgresql://USER:PASSWORD@HOST:5432/dairyos_recovery"
```

After restoration, run the DairyOS readiness checks and the persistence
regression tests against the recovered database. Do not overwrite the live
farm database during a recovery drill.

## Recovery acceptance criteria

1. Backup command exits successfully.
2. Backup is non-empty.
3. `pg_restore --list` succeeds.
4. Restore completes without a database error.
5. `/readiness` reports database READY.
6. Existing Animal IDs remain present and unique.
7. Milk, health, treatment/withdrawal, breeding, feed and finance records
   remain queryable.
8. Operational events/state remain queryable.
9. Application tests pass against the recovered database.

## Operational policy

Backups must be scheduled outside DairyOS application request handling and
stored on infrastructure independent of the primary database host. The
repository utility is the deterministic recovery mechanism; infrastructure
scheduling and off-site retention are deployment responsibilities.
