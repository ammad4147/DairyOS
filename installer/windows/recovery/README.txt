DairyOS farm-data protection

PRIMARY DATA ROOT
%ProgramData%\DairyOS

The application is installed under Program Files, but farm data is NOT stored
there. These survive normal uninstall and application reinstallation:

  postgresql-data\       live PostgreSQL cluster
  backups\               rolling logical backups
  desktop-config.json    database identity/credential metadata
  backup-settings.json   optional secondary backup destination
  recovery\              recovery tooling

UNINSTALL
The DairyOS uninstaller never deletes %ProgramData%\DairyOS. It attempts a
final pg_dump first and aborts the uninstall if that backup fails.

SECONDARY BACKUP
For protection against physical disk failure, configure a second location in:

  C:\ProgramData\DairyOS\backup-settings.json

Example:
{
  "secondary_backup_dir": "D:\\DairyOS-Farm-Backups"
}

A second physical disk, NAS, or protected cloud-synchronised location is
recommended. No application can guarantee survival if the only physical disk
is destroyed; a secondary copy is therefore part of the data-protection model.

RESTORE
Use DairyOS-Data-Restore.ps1 only for deliberate database recovery. It requires
typing RESTORE-DATABASE because restoring replaces the current database.
