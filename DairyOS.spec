# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import collect_submodules


# The spec is part of the repository and must remain portable across
# developer/build machines. SPECPATH is provided by PyInstaller and points
# at the directory containing this .spec file.
ROOT = Path(SPECPATH).resolve()
ICON = ROOT / "assets" / "dairyos-cow.ico"

if not ICON.is_file():
    raise FileNotFoundError(f"DairyOS launcher icon is missing: {ICON}")


datas = [
    (str(ROOT / "alembic.ini"), "."),
    (str(ROOT / "db_migrations"), "db_migrations"),
    (str(ROOT / "docs" / "training"), "docs/training"),
    (str(ROOT / "src" / "DairyOS.Web" / "dist"), "src/DairyOS.Web/dist"),
]
binaries = []
hiddenimports = []
# The normal farm runtime carries the protected lifecycle and recovery
# services used by Settings. There is no standalone operator Admin module to
# package.
hiddenimports += collect_submodules("dairyos")
hiddenimports += collect_submodules("alembic")
hiddenimports += collect_submodules("sqlalchemy")
tmp_ret = collect_all("webview")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Search is part of the normal application runtime. Collect the client package
# explicitly so the frozen desktop does not depend on a developer Python
# installation or dynamic import discovery at runtime.
tmp_ret = collect_all("elasticsearch")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


PRODUCTION_EXCLUDES = [
    "pytest",
    "tests",
]

# A release build must carry the Assistant runtime. This escape hatch exists so
# a developer can build the application without a 1.28 GB download, and it is
# deliberately loud: the resulting package ships an Assistant that cannot
# answer, and the release certification at AA-13 rejects it.
ALLOW_ASSISTANT_WITHOUT_RUNTIME = os.environ.get(
    "DAIRYOS_ALLOW_ASSISTANT_WITHOUT_RUNTIME", ""
).strip().lower() in {"1", "true", "yes"}


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

# ---------------------------------------------------------------------------
# The Assistant, built as its own executable from its own dependency graph.
#
# Everything above shares `binaries` and `hiddenimports`, which carry the whole
# operational graph: dairyos, SQLAlchemy, Alembic and the Elasticsearch client.
# The Assistant deliberately shares none of it. Its Analysis is built from
# nothing but its own package, and the modules that would give it a route to
# farm data are named as excludes so that an accidental import becomes a build
# failure rather than a shipped capability.
#
# This is why `dairyos_assistant` is a sibling package rather than a subpackage:
# `collect_submodules("dairyos")` above cannot reach it, so the operational
# collection and this one cannot bleed into each other.
#
# The rule this encodes is the project's first principle. A capability the
# Assistant must never use should not exist in its runtime, and the cheapest
# place to enforce that is the build.
ASSISTANT_FORBIDDEN = [
    "dairyos",
    "sqlalchemy",
    "alembic",
    "psycopg",
    "psycopg2",
    "elasticsearch",
    "dotenv",
    "webview",
    "fastapi",
    "starlette",
    "uvicorn",
]

# Operator decision of 2026-09-18: the installed machine must need nothing
# external. The model weights and the llama.cpp server are therefore carried
# inside the package rather than fetched after installation, which takes the
# installer from roughly 98 MiB to roughly 1.4 GB.
#
# They still have to be downloaded once on the BUILD machine, because a 1.28 GB
# file cannot live in git. Build-DairyOS-Desktop.ps1 fetches them and verifies
# the pinned sha256 values before this spec runs. The two are different
# problems: a build machine has a network, a farm does not.
ASSISTANT_RUNTIME = ROOT / "runtime" / "assistant"
ASSISTANT_MODEL = ASSISTANT_RUNTIME / "model" / "Qwen3-1.7B-Q4_K_M.gguf"
ASSISTANT_SERVER = ASSISTANT_RUNTIME / "llama" / "llama-server.exe"

assistant_runtime_datas = []
for _path, _dest in ((ASSISTANT_MODEL, "assistant-runtime/model"),
                     (ASSISTANT_SERVER, "assistant-runtime/llama")):
    if _path.is_file():
        assistant_runtime_datas.append((str(_path), _dest))
    elif not ALLOW_ASSISTANT_WITHOUT_RUNTIME:
        raise FileNotFoundError(
            f"Assistant runtime artefact missing: {_path}. "
            "Run scripts/Get-AssistantRuntime.ps1 to download and verify it, or set "
            "DAIRYOS_ALLOW_ASSISTANT_WITHOUT_RUNTIME=1 to build a package whose "
            "Assistant cannot answer."
        )

assistant_a = Analysis(
    [str(ROOT / "src" / "dairyos_assistant" / "service.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[
        # The corpus is the Assistant's entire subject matter. It is resolved
        # at runtime from sys._MEIPASS by dairyos_assistant.service.corpus_root.
        (str(ROOT / "docs" / "assistant-knowledge"), "assistant-knowledge"),
    ] + assistant_runtime_datas,
    hiddenimports=collect_submodules("dairyos_assistant"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=PRODUCTION_EXCLUDES + ASSISTANT_FORBIDDEN,
    noarchive=False,
    optimize=0,
)
assistant_pyz = PYZ(assistant_a.pure)
assistant_exe = EXE(
    assistant_pyz,
    assistant_a.scripts,
    [],
    exclude_binaries=True,
    name="DairyOSAssistant",
    icon=str(ICON),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    # The Assistant speaks JSON lines over stdin and stdout and is started by
    # the DairyOS backend, never by the operator, so it has no console of its
    # own to show.
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
