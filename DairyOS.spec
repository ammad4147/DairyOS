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
hiddenimports += collect_submodules("dairyos")
hiddenimports += collect_submodules("alembic")
hiddenimports += collect_submodules("sqlalchemy")
tmp_ret = collect_all("webview")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


a = Analysis(
    [str(ROOT / "src" / "dairyos" / "windows" / "supervisor.py")],
    pathex=[str(ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DairyOS",
)
