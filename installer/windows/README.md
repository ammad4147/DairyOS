# DairyOS Windows installer

This package turns the existing DairyOS React/FastAPI application into a conventional Windows desktop application without changing DairyOS business logic or user-interface layout.

## User experience

1. Run `DairyOS-Setup-0.1.0-Windows-x64.exe`.
2. The installer creates a normal Windows application and Desktop/Start Menu shortcuts.
3. Double-click **DairyOS** to open the application in its own desktop window.
4. PostgreSQL, the DairyOS backend, and the existing React frontend run locally behind that window.
5. Windows Apps & Features contains the normal **DairyOS Uninstall** entry.

## Farm-data safety model

The application and the farm database are deliberately separated:

- Program files: `%ProgramFiles%\DairyOS`
- Farm data: `%ProgramData%\DairyOS`
- PostgreSQL cluster: `%ProgramData%\DairyOS\postgresql-data`
- Rolling backups: `%ProgramData%\DairyOS\backups`
- Recovery tools: `%ProgramData%\DairyOS\recovery`

The uninstall operation removes the application only. It does **not** delete `%ProgramData%\DairyOS`.

Before uninstall, the custom NSIS uninstaller executes a final PostgreSQL logical backup. If that backup fails, uninstall is aborted.

Before every normal application startup against an existing database, the desktop shell creates a `prestart` logical backup. This is intentional because DairyOS startup may perform schema migrations.

For true protection against physical disk destruction, configure a secondary backup location in `%ProgramData%\DairyOS\backup-settings.json`, preferably on a different physical disk, NAS, or protected cloud-synchronised location.

## Recovery

`DairyOS-Data-Restore.ps1` is deliberately destructive and requires the operator to type `RESTORE-DATABASE`. The backup file itself is never altered.

## Existing farm installation

Reinstalling DairyOS over an existing machine must reuse the existing `%ProgramData%\DairyOS` data directory. The installer must never initialize a second empty farm database when the existing PostgreSQL cluster is present.

## Build

The Windows CI workflow performs:

- Python dependency installation
- full pytest regression
- PyInstaller backend packaging
- frontend typecheck
- frontend production build
- PostgreSQL Windows x64 binary packaging
- Electron/NSIS installer creation
- installer/uninstaller data-safety smoke tests

The PostgreSQL Windows binaries are pulled from EDB's current binary distribution during the build rather than stored in the DairyOS source repository.
