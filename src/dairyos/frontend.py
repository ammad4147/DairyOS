"""Resolve and mount the production React build inside the FastAPI application."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles


def frontend_dist_candidates() -> list[Path]:
    """Return source and frozen-runtime candidates for the React dist tree."""
    candidates: list[Path] = []
    override = os.environ.get("DAIRYOS_FRONTEND_DIST")
    if override:
        candidates.append(Path(override).expanduser())

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        base = Path(meipass)
        candidates.extend((base / "DairyOS.Web" / "dist", base / "dist"))

    here = Path(__file__).resolve()
    repo_root = here.parents[2]
    candidates.append(repo_root / "DairyOS.Web" / "dist")
    candidates.append(repo_root / "src" / "DairyOS.Web" / "dist")
    candidates.append(Path.cwd() / "src" / "DairyOS.Web" / "dist")
    return candidates


def resolve_frontend_dist() -> Path | None:
    """Find a valid React production build, if one is available."""
    seen: set[Path] = set()
    for candidate in frontend_dist_candidates():
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "index.html").is_file():
            return candidate
    return None


def mount_frontend(app: FastAPI) -> Path | None:
    """Mount the production UI at ``/`` without disturbing API routes.

    API routes are registered before this mount, so paths such as ``/health``
    and ``/farm/...`` remain authoritative. ``html=True`` provides the SPA
    fallback for client-side React routes.
    """
    dist = resolve_frontend_dist()
    if dist is None:
        return None

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="frontend-assets")

    app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")
    return dist


def frontend_index_response() -> FileResponse | None:
    """Return the production index file when a bundled UI is available."""
    dist = resolve_frontend_dist()
    if dist is None:
        return None
    return FileResponse(dist / "index.html")
