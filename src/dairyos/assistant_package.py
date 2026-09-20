"""Governed installation state for the optional Assistant package.

This module deliberately knows only package files and compatibility metadata;
it does not import the operational database or farm repositories.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

ASSISTANT_ROOT = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "DairyOS" / "assistant"
PACKAGE_SOURCE = Path(
    os.environ.get("DAIRYOS_ASSISTANT_PACKAGE", "")
) if os.environ.get("DAIRYOS_ASSISTANT_PACKAGE", "") else None
CORE_VERSION = "0.1.0"


def manifest_path() -> Path:
    return ASSISTANT_ROOT / "assistant-manifest.json"


def read_manifest() -> dict | None:
    path = manifest_path()
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def status() -> dict:
    manifest = read_manifest()
    return {
        "installed": manifest is not None,
        "manifest": manifest,
        "status": "INSTALLED" if manifest is not None else "NOT_INSTALLED",
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _compatible(manifest: dict) -> bool:
    return str(manifest.get("compatible_core", "")).startswith(">=0.1.0")


def install(source: Path | None = None) -> dict:
    package = source or PACKAGE_SOURCE
    if package is None or not package.is_file():
        raise FileNotFoundError("No approved Assistant package source is configured.")
    expected = Path(str(package) + ".sha256")
    if not expected.is_file():
        raise ValueError("Assistant package SHA-256 sidecar is required.")
    fields = expected.read_text(encoding="utf-8").strip().split()
    declared = fields[0].lower() if fields else ""
    if len(declared) != 64 or any(ch not in "0123456789abcdef" for ch in declared):
        raise ValueError("Assistant package SHA-256 sidecar is invalid.")
    actual = _sha256(package)
    if declared != actual:
        raise ValueError("Assistant package SHA-256 verification failed.")

    staging_parent = ASSISTANT_ROOT.parent / ".assistant-staging"
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="package-", dir=staging_parent))
    try:
        with zipfile.ZipFile(package) as archive:
            archive.extractall(staging)
        candidates = list(staging.rglob("assistant-manifest.json"))
        if len(candidates) != 1:
            raise ValueError("Assistant package manifest is missing or ambiguous.")
        # PowerShell's UTF-8 output on supported Windows builds may include a
        # BOM. It is still the package's JSON manifest, not a reason to reject
        # an otherwise verified artifact.
        manifest = json.loads(candidates[0].read_text(encoding="utf-8-sig"))
        if not isinstance(manifest, dict) or not _compatible(manifest):
            raise ValueError("Assistant package is incompatible with this Core.")
        payload = candidates[0].parent
        if not (payload / "DairyOSAssistant.exe").is_file():
            raise ValueError("Assistant package executable is missing.")
        target = ASSISTANT_ROOT.parent / ".assistant-active"
        backup = ASSISTANT_ROOT.parent / ".assistant-previous"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(payload, target)
        if backup.exists():
            shutil.rmtree(backup)
        try:
            if ASSISTANT_ROOT.exists():
                ASSISTANT_ROOT.replace(backup)
            target.replace(ASSISTANT_ROOT)
        except Exception:
            if ASSISTANT_ROOT.exists():
                shutil.rmtree(ASSISTANT_ROOT, ignore_errors=True)
            if backup.exists():
                backup.replace(ASSISTANT_ROOT)
            raise
        finally:
            if backup.exists():
                shutil.rmtree(backup, ignore_errors=True)
        return status()
    finally:
        shutil.rmtree(staging, ignore_errors=True)
