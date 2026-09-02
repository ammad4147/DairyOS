# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import collect_submodules


# The spec is part of the repository and must remain portable across
# developer/build machines. SPECPATH is provided by PyInstaller and points
# at the directory containing this .spec file.
ROOT = Path(SPECPATH).resolve()


datas = [
    (str(ROOT / "alembic.ini"), "."),
    (str(ROOT / "db_migrations"), "db_migrations"),
    (str(ROOT / "src" / "DairyOS.Web" / "dist"), "src/DairyOS.Web/dist"),
]
binaries = []
hiddenimports = []
# The normal farm runtime must not carry the destructive Admin Tool simply
# because it lives under the same Python package.  Admin/reset functionality is
# built and distributed separately under DairyOS-Admin.
hiddenimports += [
    module
    for module in collect_submodules("dairyos")
    if module != "dairyos.admin" and not module.startswith("dairyos.admin.")
]
hiddenimports += collect_submodules("alembic")
hiddenimports += collect_submodules("sqlalchemy")
tmp_ret = collect_all("webview")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


PRODUCTION_EXCLUDES = [
    "dairyos.admin",
    "pytest",
    "tests",
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

# Automatic backups run outside the normal application process.  Shipping a
# dedicated worker keeps the Task Scheduler entry simple and prevents the farm
# owner from needing Python, a repository checkout, or developer tooling.  It
# uses the same production exclusions as DairyOS.exe and therefore also cannot
# import the destructive Admin Tool.
backup_a = Analysis(
    [str(ROOT / "src" / "dairyos" / "windows" / "backup_task.py")],
    pathex=[str(ROOT / "src")],
    binaries=binaries,
    datas=[
        (str(ROOT / "alembic.ini"), "."),
        (str(ROOT / "db_migrations"), "db_migrations"),
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
