DairyOS farm-data protection

PRIMARY DATA ROOT
%ProgramData%\DairyOS

The DairyOS application is installed under Program Files, but farm data is NOT
stored there. The following survive application repair, reinstallation, and
normal uninstallation:

- postgresql-data\       live PostgreSQL cluster
- backups\               rolling logical database backups
- desktop-config.json    database identity/credential metadata
- backup-settings.json   optional secondary backup destination
- recovery\              recovery tooling

UNINSTALL RULE
The DairyOS uninstaller deliberately leaves %ProgramData%\DairyOS intact.
The uninstaller first requests a final pg_dump backup. If that backup fails,
uninstallation is aborted.

RESTORE
Use DairyOS-Data-Restore.ps1 only when a database restore is actually required.
It requires typing RESTORE-DATABASE because it replaces the current database.

SECONDARY BACKUP
For protection from physical disk failure, configure a second location in:
%ProgramData%\DairyOS\backup-settings.json

Example:
{
  "secondary_backup_dir": "D:\\DairyOS-Farm-Backups"
}

A second disk, NAS, or protected cloud-synchronised location is recommended.
No software can guarantee data survival if the only storage device itself is
physically destroyed; the secondary copy addresses that failure mode.
