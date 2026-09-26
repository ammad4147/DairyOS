# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all


# The spec is part of the repository and must remain portable across
# developer/build machines. SPECPATH is provided by PyInstaller and points
# at the directory containing this .spec file.
ROOT = Path(SPECPATH).resolve()
ICON = ROOT / "assets" / "dairyos-cow.ico"

if not ICON.is_file():
    raise FileNotFoundError(f"DairyOS launcher icon is missing: {ICON}")


MIGRATION_DATA = [
    (str(path), str(path.parent.relative_to(ROOT)))
    for path in (ROOT / "db_migrations").rglob("*.py")
    if path.is_file()
]
datas = [
    (str(ROOT / "alembic.ini"), "."),
    *MIGRATION_DATA,
    (str(ROOT / "src" / "DairyOS.Web" / "dist"), "src/DairyOS.Web/dist"),
]
binaries = []
# This reviewed inventory was extracted from the previous production archive's
# bytecode graph using supervisor, backend, backup-worker and Alembic model
# roots, with parent packages and from-package submodules included. Keeping the
# complete known-live set explicit removes the blanket dairyos collector while
# retaining every previously identified runtime module. Runtime/package tests
# remain the release gate before any later inventory pruning.
hidden_import_inventory = ROOT / "packaging" / "desktop-hiddenimports.txt"
if not hidden_import_inventory.is_file():
    raise FileNotFoundError(f"Desktop hidden-import inventory is missing: {hidden_import_inventory}")
hiddenimports = [
    line.strip()
    for line in hidden_import_inventory.read_text(encoding="utf-8").splitlines()
    if line.strip()
]
if len(hiddenimports) != len(set(hiddenimports)):
    raise ValueError("Desktop hidden-import inventory contains duplicate module names")
# URL handling can request this codec dynamically in a frozen build. Keep it
# explicit so packaged Windows runtime does not report "unknown encoding: idna".
hiddenimports.append("encodings.idna")
tmp_ret = collect_all("webview")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

PRODUCTION_EXCLUDES = [
    "pytest",
    "tests",
    "alembic.testing",
    "sqlalchemy.testing",
    "mypy",
]

a = Analysis(
    [str(ROOT / "src" / "dairyos" / "windows" / "supervisor.py")],
    pathex=[str(ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=PRODUCTION_EXCLUDES,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DairyOS",
    icon=str(ICON),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Automatic backups run outside the normal application process. Shipping a
# dedicated worker keeps the Task Scheduler entry simple and prevents the farm
# owner from needing Python, a repository checkout, or developer tooling.
backup_a = Analysis(
    [str(ROOT / "src" / "dairyos" / "windows" / "backup_task.py")],
    pathex=[str(ROOT / "src")],
    binaries=binaries,
    datas=[
        (str(ROOT / "alembic.ini"), "."),
        *MIGRATION_DATA,
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=PRODUCTION_EXCLUDES,
    noarchive=False,
    optimize=0,
)
backup_pyz = PYZ(backup_a.pure)
backup_exe = EXE(
    backup_pyz,
    backup_a.scripts,
    [],
    exclude_binaries=True,
    name="DairyOSBackup",
    icon=str(ICON),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    backup_exe,
    a.binaries,
    a.datas,
    backup_a.binaries,
    backup_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DairyOS",
)
