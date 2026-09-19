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
    expected = package.with_suffix(".sha256")
    if expected.is_file():
        declared = expected.read_text(encoding="utf-8").strip().split()[0].lower()
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
        manifest = json.loads(candidates[0].read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or not _compatible(manifest):
            raise ValueError("Assistant package is incompatible with this Core.")
        payload = candidates[0].parent
        target = ASSISTANT_ROOT.parent / ".assistant-active"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(payload, target)
        if ASSISTANT_ROOT.exists():
            shutil.rmtree(ASSISTANT_ROOT)
        target.replace(ASSISTANT_ROOT)
        return status()
    finally:
        shutil.rmtree(staging, ignore_errors=True)
