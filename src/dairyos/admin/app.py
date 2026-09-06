"""Standalone authenticated web UI for DairyOS administration."""

from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
import secrets
import time

from dairyos.admin import auth
from dairyos.admin.service import AdminService, PURGE_CONFIRMATION, RESET_CONFIRMATION
from dairyos.lifecycle.manager import LifecycleManager

SESSION_TTL_SECONDS = 30 * 60
_SESSIONS: dict[str, float] = {}


def _manager() -> LifecycleManager:
    installation_root = os.environ.get("DAIRYOS_INSTALLATION_ROOT", str(Path.cwd()))
    data_root = os.environ.get("DAIRYOS_DATA_ROOT") or os.environ.get("DAIRYOS_DATA_DIR")
    return LifecycleManager(installation_root, data_root=data_root)


def _service() -> AdminService:
    return AdminService(_manager())


def _esc(value: object) -> str:
    return html.escape(str(value or ""))


def _shell(body: str, message: str = "") -> str:
    notice = f"<pre>{_esc(message)}</pre>" if message else ""
    return f"""<!doctype html><html><head><meta charset='utf-8'>
<title>DairyOS Administration</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#0f172a;color:#e2e8f0;margin:0}}
main{{max-width:1100px;margin:28px auto;padding:20px}} h1{{margin-bottom:4px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}}
section{{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:16px}}
button{{padding:9px 13px;margin:4px 0;border:0;border-radius:6px;cursor:pointer}}
input{{padding:9px;margin:4px 0;width:calc(100% - 20px);background:#0f172a;color:#e2e8f0;border:1px solid #475569;border-radius:5px}}
.danger{{background:#991b1b;color:white}} .normal{{background:#334155;color:white}}
pre{{white-space:pre-wrap;background:#020617;padding:12px;border-radius:6px;overflow:auto}}
small{{color:#94a3b8}} a{{color:#7dd3fc}} code{{color:#fbbf24}}
</style></head><body><main><h1>DairyOS Administration</h1>
<p>Standalone privileged lifecycle and recovery administration.</p>{notice}{body}</main></body></html>"""


def _setup_page(message: str = "") -> str:
    return _shell(
        """<section><h2>First-run Administrator Setup</h2>
<small>Create the password required for every future Admin Tool session. A recovery key will be shown once after setup.</small>
<form method='post' action='/setup'>
<input type='password' name='password' placeholder='Administrator password (12+ characters)' autocomplete='new-password' required>
<input type='password' name='confirmation' placeholder='Confirm administrator password' autocomplete='new-password' required>
<button class='normal'>Create Administrator Password</button></form></section>""",
        message,
    )


def _login_page(message: str = "") -> str:
    return _shell(
        """<section><h2>Administrator Login</h2>
<form method='post' action='/login'>
<input type='password' name='password' placeholder='Administrator password' autocomplete='current-password' required>
<button class='normal'>Unlock Admin Tool</button></form>
<p><a href='/recover'>Forgot administrator password?</a></p></section>""",
        message,
    )


def _recover_page(message: str = "") -> str:
    return _shell(
        """<section><h2>Recover Administrator Password</h2>
<small>Enter the recovery key issued at setup or at the last password change/recovery.</small>
<form method='post' action='/recover'>
<input name='recovery_key' placeholder='Recovery key' autocomplete='off' required>
<input type='password' name='new_password' placeholder='New administrator password' autocomplete='new-password' required>
<input type='password' name='confirmation' placeholder='Confirm new password' autocomplete='new-password' required>
<button class='normal'>Reset Administrator Password</button></form>
<p><a href='/'>Back to login</a></p></section>""",
        message,
    )


def _dashboard(message: str = "") -> str:
    reset_token = _esc(RESET_CONFIRMATION)
    purge_token = _esc(PURGE_CONFIRMATION)
    audit_rows = auth.read_audit(25)
    audit_text = "\n".join(
        f"{row.get('timestamp')}  {row.get('event')}  {'PASS' if row.get('success') else 'FAIL'}  {row.get('detail','')}"
        for row in reversed(audit_rows)
    ) or "No administrative audit events yet."
    body = f"""<p><a href='/logout'>Lock Admin Tool</a></p>
<div class='grid'>
<section><h2>Health</h2><form method='post' action='/validate'><button class='normal'>Validate Installation & Database</button></form></section>
<section><h2>Create Verified Backup</h2><form method='post' action='/backup'><button class='normal'>Create Backup</button></form></section>
<section><h2>Restore Verified Backup</h2><form method='post' action='/restore'>
<input name='backup' placeholder='Full verified backup directory path' required>
<input type='password' name='password' placeholder='Re-enter administrator password' required>
<button class='danger'>Restore Backup</button></form></section>
<section><h2>Rollback</h2><form method='post' action='/rollback'>
<input name='backup' placeholder='Full verified backup directory path' required>
<input type='password' name='password' placeholder='Re-enter administrator password' required>
<button class='danger'>Rollback to Backup</button></form></section>
<section><h2>Reset Application Data</h2><small>Creates and verifies an external recovery artifact before mutation.</small>
<form method='post' action='/reset'><input type='password' name='password' placeholder='Re-enter administrator password' required>
<input name='confirm' placeholder='{reset_token}' required><button class='danger'>Reset Application Data</button></form></section>
<section><h2>Permanent Purge</h2><small>Creates an external recovery artifact before deleting the data root.</small>
<form method='post' action='/purge'><input type='password' name='password' placeholder='Re-enter administrator password' required>
<input name='confirm' placeholder='{purge_token}' required><button class='danger'>Permanently Purge Data</button></form></section>
<section><h2>Uninstall — Keep Data</h2><form method='post' action='/uninstall'>
<input type='password' name='password' placeholder='Re-enter administrator password' required>
<button class='danger'>Uninstall and Keep Data</button></form></section>
<section><h2>Change Admin Password</h2><form method='post' action='/change-password'>
<input type='password' name='current' placeholder='Current password' required>
<input type='password' name='new_password' placeholder='New password' required>
<input type='password' name='confirmation' placeholder='Confirm new password' required>
<button class='normal'>Change Password</button></form></section>
</div>
<section style='margin-top:14px'><h2>Administrative Audit</h2><pre>{_esc(audit_text)}</pre></section>"""
    return _shell(body, message)


def _session_from_request(request) -> str | None:
    token = request.cookies.get("dairyos_admin_session", "")
    expiry = _SESSIONS.get(token)
    if not token or expiry is None:
        return None
    if expiry < time.time():
        _SESSIONS.pop(token, None)
        return None
    _SESSIONS[token] = time.time() + SESSION_TTL_SECONDS
    return token


def _require_session(request) -> None:
    if _session_from_request(request) is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Administrator authentication required.")


def create_app():
    try:
        from fastapi import FastAPI, Form, Request
        from fastapi.responses import HTMLResponse, RedirectResponse
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("FastAPI is required for the DairyOS Admin Tool") from exc

    app = FastAPI(title="DairyOS Administration", docs_url=None, redoc_url=None)

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        if not auth.configured():
            return _setup_page()
        if _session_from_request(request):
            return _dashboard()
        return _login_page()

    @app.post("/setup", response_class=HTMLResponse)
    def setup(password: str = Form(""), confirmation: str = Form("")):
        try:
            recovery = auth.setup(password, confirmation)
            return _login_page(
                "Administrator password configured. SAVE THIS NEW RECOVERY KEY NOW: "
                + recovery
            )
        except Exception as exc:
            return _setup_page(f"Setup failed: {exc}")

    @app.post("/login")
    def login(password: str = Form("")):
        if not auth.configured():
            return RedirectResponse("/", status_code=303)
        if not auth.verify_password(password):
            return HTMLResponse(_login_page("Authentication failed."), status_code=401)
        token = secrets.token_urlsafe(32)
        _SESSIONS[token] = time.time() + SESSION_TTL_SECONDS
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(
            "dairyos_admin_session",
            token,
            httponly=True,
            samesite="strict",
            max_age=SESSION_TTL_SECONDS,
        )
        return response

    @app.get("/logout")
    def logout(request: Request):
        token = request.cookies.get("dairyos_admin_session", "")
        _SESSIONS.pop(token, None)
        response = RedirectResponse("/", status_code=303)
        response.delete_cookie("dairyos_admin_session")
        auth.record_audit("admin-logout", success=True)
        return response

    @app.get("/recover", response_class=HTMLResponse)
    def recover_page():
        return _recover_page()

    @app.post("/recover", response_class=HTMLResponse)
    def recover(
        recovery_key: str = Form(""),
        new_password: str = Form(""),
        confirmation: str = Form(""),
    ):
        try:
            next_key = auth.recover_password(recovery_key, new_password, confirmation)
            _SESSIONS.clear()
            return _login_page(
                "Password recovered. SAVE THIS NEW RECOVERY KEY NOW: " + next_key
            )
        except Exception as exc:
            return _recover_page(f"Recovery failed: {exc}")

    @app.post("/validate", response_class=HTMLResponse)
    def validate(request: Request):
        _require_session(request)
        try:
            result = _service().status()
            auth.record_audit("validate", success=True)
            return _dashboard(str(result))
        except Exception as exc:
            auth.record_audit("validate", success=False, detail=str(exc))
            return _dashboard(f"Validation failed: {exc}")

    @app.post("/backup", response_class=HTMLResponse)
    def backup(request: Request):
        _require_session(request)
        try:
            result = _service().backup("admin")
            auth.record_audit("backup", success=True, detail=result.artifact or "")
            return _dashboard(f"{result.message}\n{result.artifact}")
        except Exception as exc:
            auth.record_audit("backup", success=False, detail=str(exc))
            return _dashboard(f"Backup failed: {exc}")

    @app.post("/restore", response_class=HTMLResponse)
    def restore(request: Request, backup: str = Form(""), password: str = Form("")):
        _require_session(request)
        try:
            auth.require_password(password, event="restore-reauth")
            result = _service().restore(backup)
            auth.record_audit("restore", success=True, detail=result.artifact or "")
            return _dashboard(f"{result.message}\n{result.artifact}")
        except Exception as exc:
            auth.record_audit("restore", success=False, detail=str(exc))
            return _dashboard(f"Restore not executed: {exc}")

    @app.post("/rollback", response_class=HTMLResponse)
    def rollback(request: Request, backup: str = Form(""), password: str = Form("")):
        _require_session(request)
        try:
            auth.require_password(password, event="rollback-reauth")
            result = _service().rollback(backup)
            auth.record_audit("rollback", success=result.success, detail=result.artifact or "")
            return _dashboard(f"{result.message}\n{result.artifact}")
        except Exception as exc:
            auth.record_audit("rollback", success=False, detail=str(exc))
            return _dashboard(f"Rollback not executed: {exc}")

    @app.post("/reset", response_class=HTMLResponse)
    def reset(request: Request, password: str = Form(""), confirm: str = Form("")):
        _require_session(request)
        try:
            auth.require_password(password, event="reset-reauth")
            result = _service().reset(confirm)
            auth.record_audit("reset", success=True, detail=result.artifact or "")
            return _dashboard(f"{result.message}\n{result.artifact or ''}")
        except Exception as exc:
            auth.record_audit("reset", success=False, detail=str(exc))
            return _dashboard(f"Reset not executed: {exc}")

    @app.post("/purge", response_class=HTMLResponse)
    def purge(request: Request, password: str = Form(""), confirm: str = Form("")):
        _require_session(request)
        try:
            auth.require_password(password, event="purge-reauth")
            result = _service().purge(confirm)
            auth.record_audit("purge", success=True, detail=result.artifact or "")
            return _dashboard(f"{result.message}\n{result.artifact or ''}")
        except Exception as exc:
            auth.record_audit("purge", success=False, detail=str(exc))
            return _dashboard(f"Purge not executed: {exc}")

    @app.post("/uninstall", response_class=HTMLResponse)
    def uninstall(request: Request, password: str = Form("")):
        _require_session(request)
        try:
            auth.require_password(password, event="uninstall-reauth")
            result = _service().uninstall()
            auth.record_audit("uninstall-keep-data", success=True)
            return _dashboard(result.message)
        except Exception as exc:
            auth.record_audit("uninstall-keep-data", success=False, detail=str(exc))
            return _dashboard(f"Uninstall failed: {exc}")

    @app.post("/change-password", response_class=HTMLResponse)
    def change_password(
        request: Request,
        current: str = Form(""),
        new_password: str = Form(""),
        confirmation: str = Form(""),
    ):
        _require_session(request)
        try:
            recovery = auth.change_password(current, new_password, confirmation)
            _SESSIONS.clear()
            return _login_page(
                "Password changed. SAVE THIS NEW RECOVERY KEY NOW: " + recovery
            )
        except Exception as exc:
            return _dashboard(f"Password change failed: {exc}")

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="DairyOS standalone administration tool")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18082)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        raise SystemExit("DairyOS Admin Tool is restricted to loopback hosts.")
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("uvicorn is required") from exc
    uvicorn.run(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
