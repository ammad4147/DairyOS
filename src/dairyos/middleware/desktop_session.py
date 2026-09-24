"""A per-launch capability for the login-free desktop, never served by HTTP."""
import logging
import os
import secrets
import sys

from starlette.responses import JSONResponse

from dairyos.platform.runtime_mode import RuntimeMode, resolve_runtime_mode

SESSION_ENV = "DAIRYOS_DESKTOP_SESSION_TOKEN"
SESSION_HEADER = "X-DairyOS-Desktop-Session"

LOG = logging.getLogger(__name__)

# Static asset paths that are always publicly readable without a session token.
_PUBLIC_EXACT = frozenset({
    "/",
    "/index.html",
    "/health",
    "/readiness",
    "/favicon.ico",
    "/manifest.json",
    "/dairyos-cow.svg",
    "/serviceWorker.js",
})

_PUBLIC_PREFIXES = (
    "/assets/",
)

_PUBLIC_EXTENSIONS = frozenset({
    ".js", ".css", ".svg", ".png", ".ico", ".woff", ".woff2", ".ttf", ".map",
})


def _is_public_read(method: str, path: str) -> bool:
    """Return whether this request targets a publicly readable resource."""
    if method not in {"GET", "HEAD"}:
        return False
    if path in _PUBLIC_EXACT:
        return True
    for prefix in _PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    # Allow direct access to static file extensions (fonts, scripts, etc.)
    dot = path.rfind(".")
    if dot != -1 and path[dot:].lower() in _PUBLIC_EXTENSIONS:
        return True
    return False


async def enforce_desktop_session(request, call_next):
    # Hosted requests use the named-operator authentication gate instead of the
    # per-launch capability that only the Windows supervisor can provide.
    if resolve_runtime_mode() is RuntimeMode.HOSTED:
        return await call_next(request)

    # Browser mode is explicitly selected by the local Windows supervisor.
    # It must use the named human-session/PIN middleware instead of the
    # login-free native desktop capability.
    if os.getenv("DAIRYOS_BROWSER_MODE") == "1":
        return await call_next(request)

    token = os.environ.get(SESSION_ENV, "")
    production = bool(getattr(sys, "frozen", False)) or os.getenv(
        "DAIRYOS_ENV", "development"
    ).lower() != "development"
    path = request.url.path

    # Public resources never require a session token.
    if _is_public_read(request.method, path):
        return await call_next(request)

    # In non-production mode with no token configured, allow all requests.
    if not token and not production:
        return await call_next(request)

    supplied = request.headers.get(SESSION_HEADER, "")
    if token and secrets.compare_digest(supplied, token):
        # Prevent a credential-bearing browser request from another origin.
        origin = request.headers.get("origin")
        if origin and origin != str(request.base_url).rstrip("/"):
            return JSONResponse(
                {"detail": "Desktop session origin mismatch."}, status_code=403
            )
        return await call_next(request)

    return JSONResponse(
        {
            "detail": "Open DairyOS through its desktop application to access this farm."
        },
        status_code=401,
    )
