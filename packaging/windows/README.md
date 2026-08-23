# DairyOS Windows Installer

This package is designed for a normal Windows installation with a Start Menu/Desktop launch experience and an Add/Remove Programs uninstall entry.

## Data-safety contract

- Application binaries live under `%ProgramFiles%\DairyOS`.
- All farm data, database cluster files, backups, and recovery evidence live under `%ProgramData%\DairyOS`.
- Uninstall removes application files only. It never removes `%ProgramData%\DairyOS`.
- Before uninstall, the uninstaller requests a final database backup. If that backup fails, uninstall is aborted.
- Reinstallation detects the existing `%ProgramData%\DairyOS` database and reuses it; it does not create a second farm database.

The installer bundles PostgreSQL Windows x86-64 binaries through the official EDB PostgreSQL installer. PostgreSQL's Windows installer supports unattended installation and an explicit `--datadir` for the database cluster. citeturn720275search1turn720275search5

NSIS is used for the outer installer/uninstaller. NSIS installers and uninstallers support normal interactive use and silent `/S` operation for acceptance testing. citeturn562267search2
