"""Standalone web UI for DairyOS administration.

Run with ``dairyos-admin``. This module is not imported by the operational
DairyOS web application.
"""

from __future__ import annotations

import argparse
import html
import os
import sys
from pathlib import Path

from dairyos.admin.service import AdminService
from dairyos.lifecycle.manager import LifecycleManager, LifecycleError


def _manager() -> LifecycleManager:
    installation_root = os.environ.get("DAIRYOS_INSTALLATION_ROOT", Path.cwd())
    data_root = os.environ.get("DAIRYOS_DATA_ROOT")
    return LifecycleManager(installation_root, data_root=data_root)


def _page(message: str = "") -> str:
    safe = html.escape(message)
    return f"""<!doctype html><html><head><meta charset='utf-8'>
<title>DairyOS Administration</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#0f172a;color:#e2e8f0;margin:0}}
main{{max-width:1000px;margin:40px auto;padding:24px}} h1{{margin-bottom:4px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}}
section{{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:18px}}
button{{padding:10px 14px;margin:4px;border:0;border-radius:6px;cursor:pointer}}
.danger{{background:#991b1b;color:white}} .normal{{background:#334155;color:white}}
pre{{white-space:pre-wrap;background:#020617;padding:12px;border-radius:6px}}
</style></head><body><main><h1>DairyOS Administration</h1>
<p>Standalone lifecycle and recovery administration. This is not part of the operational farm UI.</p>
{('<pre>'+safe+'</pre>') if safe else ''}
<div class='grid'>
<section><h2>Health</h2><form method='post' action='/validate'><button class='normal'>Validate Installation</button></form></section>
<section><h2>Recovery</h2><form method='post' action='/backup'><button class='normal'>Create Backup</button></form></section>
<section><h2>Restore</h2><p>Use the CLI for an explicit backup path.</p></section>
<section><h2>Destructive Operations</h2><form method='post' action='/reset'><button class='danger'>Reset Application Data</button></form><form method='post' action='/purge'><button class='danger'>Purge Data</button></form></section>
<section><h2>Uninstall</h2><form method='post' action='/uninstall'><button class='normal'>Uninstall — Keep Data</button></form></section>
</div></main></body></html>"""


def create_app():
    try:
        from fastapi import FastAPI, Form
        from fastapi.responses import HTMLResponse
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("FastAPI is required for the DairyOS Admin Tool") from exc

    app = FastAPI(title="DairyOS Administration", docs_url=None, redoc_url=None)

    @app.get("/", response_class=HTMLResponse)
    def index():
        return _page()

    @app.post("/validate", response_class=HTMLResponse)
    def validate():
        try:
            result = AdminService(_manager()).status()
            return _page(str(result))
        except Exception as exc:
            return _page(f"Validation failed: {exc}")

    @app.post("/backup", response_class=HTMLResponse)
    def backup():
        try:
            result = AdminService(_manager()).backup("admin")
            return _page(f"{result.message}\n{result.artifact}")
        except Exception as exc:
            return _page(f"Backup failed: {exc}")

    @app.post("/reset", response_class=HTMLResponse)
    def reset(confirm: str = Form("")):
        try:
            result = AdminService(_manager()).reset(confirm)
            return _page(f"{result.message}\n{result.artifact or ''}")
        except Exception as exc:
            return _page(f"Reset not executed: {exc}")

    @app.post("/purge", response_class=HTMLResponse)
    def purge(confirm: str = Form("")):
        try:
            result = AdminService(_manager()).purge(confirm)
            return _page(f"{result.message}\n{result.artifact or ''}")
        except Exception as exc:
            return _page(f"Purge not executed: {exc}")

    @app.post("/uninstall", response_class=HTMLResponse)
    def uninstall():
        try:
            result = AdminService(_manager()).uninstall()
            return _page(result.message)
        except Exception as exc:
            return _page(f"Uninstall failed: {exc}")

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="DairyOS standalone administration tool")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18082)
    args = parser.parse_args()
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("uvicorn is required") from exc
    uvicorn.run(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
