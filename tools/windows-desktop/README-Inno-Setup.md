# Windows installer build prerequisite

The installer build requires the Inno Setup command-line compiler `ISCC.exe`.

Supported major versions: Inno Setup 6.x and 7.x.

The build script discovers `ISCC.exe` from the standard Program Files locations for both major versions and from `PATH` as a fallback.
