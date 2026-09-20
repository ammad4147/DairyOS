# -*- mode: python ; coding: utf-8 -*-
"""Standalone Architecture B Assistant package."""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).resolve()
ICON = ROOT / "assets" / "dairyos-cow.ico"
ALLOW_MISSING_RUNTIME = os.environ.get(
    "DAIRYOS_ALLOW_ASSISTANT_WITHOUT_RUNTIME", ""
).strip().lower() in {"1", "true", "yes"}

runtime = ROOT / "runtime" / "assistant"
model = runtime / "model" / "Qwen3-1.7B-Q4_K_M.gguf"
server = runtime / "llama" / "llama-server.exe"
assistant_runtime_datas = []
if model.is_file():
    assistant_runtime_datas.append((str(model), "assistant-runtime/model"))
elif not ALLOW_MISSING_RUNTIME:
    raise FileNotFoundError(f"Assistant runtime artifact missing: {model}")

llama_files = list((runtime / "llama").glob("*")) if (runtime / "llama").is_dir() else []
if not llama_files and not ALLOW_MISSING_RUNTIME:
    raise FileNotFoundError(f"Assistant runtime directory missing: {runtime / 'llama'}")
for path in llama_files:
    if path.is_file():
        assistant_runtime_datas.append((str(path), "assistant-runtime/llama"))

assistant = Analysis(
    [str(ROOT / "src" / "dairyos_assistant" / "service.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[(str(ROOT / "docs" / "assistant-knowledge"), "assistant-knowledge")] + assistant_runtime_datas,
    hiddenimports=collect_submodules("dairyos_assistant") + ["encodings.idna"],
    excludes=[
        "dairyos", "sqlalchemy", "alembic", "psycopg", "psycopg2",
        "elasticsearch", "dotenv", "webview", "fastapi", "starlette", "uvicorn",
        "pytest", "tests",
    ],
    noarchive=False,
)
pyz = PYZ(assistant.pure)
exe = EXE(
    pyz,
    assistant.scripts,
    [],
    exclude_binaries=True,
    name="DairyOSAssistant",
    icon=str(ICON),
    console=False,
)
coll = COLLECT(
    exe,
    assistant.binaries,
    assistant.datas,
    strip=False,
    upx=True,
    name="DairyOS-Assistant-Pack",
)
