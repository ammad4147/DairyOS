"""Every mounted API operation must be default-deny in production mode."""

import importlib
import re

from fastapi import HTTPException
from fastapi.routing import APIRoute

from dairyos.app import app
from dairyos.platform.runtime_mode import RUNTIME_MODE_ENV


HTTP_METHODS = {"get", "head", "post", "put", "patch", "delete", "options", "trace"}


def _concrete_path(path: str) -> str:
    return re.sub(r"\{[^{}]+\}", "1", path)


def _join_path(prefix: str, path: str) -> str:
    if not prefix:
        return path or "/"
    if not path or path == "/":
        return prefix
    return f"{prefix.rstrip('/')}/{path.lstrip('/')}"


def _registered_api_operations(routes, prefix: str = "") -> set[tuple[str, str]]:
    operations: set[tuple[str, str]] = set()
    for route in routes:
        if isinstance(route, APIRoute):
            path = _join_path(prefix, route.path)
            operations.update(
                (method.upper(), path)
                for method in route.methods or set()
                if method.lower() in HTTP_METHODS
            )
            continue

        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            context = getattr(route, "include_context", None)
            nested_prefix = getattr(context, "prefix", "") if context else ""
            nested_prefix = _join_path(prefix, nested_prefix) if nested_prefix else prefix
            operations.update(
                _registered_api_operations(original_router.routes, nested_prefix)
            )
    return operations


def test_every_registered_nonpublic_route_requires_human_session(
    client, monkeypatch
):
    app_module = importlib.import_module("dairyos.app")
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv("DAIRYOS_DESKTOP_SESSION_TOKEN", "route-coverage-desktop-token")

    def no_human_session(_token):
        raise HTTPException(status_code=401, detail="Human authentication required.")

    monkeypatch.setattr(app_module, "_current_session", no_human_session)
    desktop_headers = {"X-DairyOS-Desktop-Session": "route-coverage-desktop-token"}
    operations = _registered_api_operations(app.routes)

    assert operations, "Registered API route inventory must not be empty"
    public_operations = []
    for method, path in operations:
        concrete_path = _concrete_path(path)
        if app_module._is_public_human_access_request(method, concrete_path):
            assert (
                (method, concrete_path) in app_module._HUMAN_ACCESS_PUBLIC_EXACT
                or (method in {"GET", "HEAD"} and concrete_path.startswith("/assets/"))
                or (
                    method == "POST"
                    and re.fullmatch(r"/human-access/people/\d+/pin/initial", concrete_path)
                )
            ), f"Unexpected public route: {method} {concrete_path}"
            public_operations.append((method, path))

    protected = set(operations) - set(public_operations)
    assert protected, "Route inventory should include protected production operations"
    failures = []
    for method, path in sorted(protected):
        response = client.request(
            method,
            _concrete_path(path),
            headers=desktop_headers,
        )
        if response.status_code != 401:
            failures.append(f"{method} {path}: expected 401, got {response.status_code}")

    assert not failures, "Production routes bypass human-session default-deny:\n" + "\n".join(failures)


def test_hosted_mode_enforces_human_access_without_dairyos_env(client, monkeypatch):
    monkeypatch.setenv(RUNTIME_MODE_ENV, "hosted")
    monkeypatch.delenv("DAIRYOS_ENV", raising=False)
    monkeypatch.delenv("DAIRYOS_DESKTOP_SESSION_TOKEN", raising=False)

    response = client.get("/farm/animals")

    assert response.status_code == 401
    assert response.json()["detail"] == "Human authentication required"
