from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPEC).resolve().parent.parent

hiddenimports = collect_submodules("dairyos.admin") + collect_submodules("dairyos.lifecycle")

analysis = Analysis(
    [str(ROOT / "src" / "dairyos" / "admin" / "app.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="DairyOS-Admin",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
