"""A per-launch capability for the login-free desktop, never served by HTTP."""
import os
import secrets
import sys

from starlette.responses import JSONResponse

SESSION_ENV = "DAIRYOS_DESKTOP_SESSION_TOKEN"
SESSION_HEADER = "X-DairyOS-Desktop-Session"


async def enforce_desktop_session(request, call_next):
    token = os.environ.get(SESSION_ENV, "")
    production = bool(getattr(sys, "frozen", False)) or os.getenv("DAIRYOS_ENV", "development").lower() != "development"
    path = request.url.path
    public_read = request.method in {"GET", "HEAD"} and (
        path in {"/", "/index.html", "/health", "/readiness", "/favicon.ico"}
        or path.startswith("/assets/")
    )
    if public_read or (not token and not production):
        return await call_next(request)
    supplied = request.headers.get(SESSION_HEADER, "")
    if token and secrets.compare_digest(supplied, token):
        # Also prevent a credential-bearing browser request from another origin.
        origin = request.headers.get("origin")
        if origin and origin != str(request.base_url).rstrip("/"):
            return JSONResponse({"detail": "Desktop session origin mismatch."}, status_code=403)
        return await call_next(request)
    return JSONResponse({"detail": "Open DairyOS through its desktop application to access this farm."}, status_code=401)
