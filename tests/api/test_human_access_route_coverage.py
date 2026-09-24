"""Every mounted API operation must be default-deny in production mode."""

import importlib
import re

from fastapi import HTTPException

from dairyos.app import app


HTTP_METHODS = {"get", "head", "post", "put", "patch", "delete", "options", "trace"}


def _concrete_path(path: str) -> str:
    return re.sub(r"\{[^{}]+\}", "1", path)


def test_every_documented_nonpublic_route_requires_human_session(
    client, monkeypatch
):
    app_module = importlib.import_module("dairyos.app")
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv("DAIRYOS_DESKTOP_SESSION_TOKEN", "route-coverage-desktop-token")

    def no_human_session(_token):
        raise HTTPException(status_code=401, detail="Human authentication required.")

    monkeypatch.setattr(app_module, "_current_session", no_human_session)
    desktop_headers = {"X-DairyOS-Desktop-Session": "route-coverage-desktop-token"}
    operations = [
        (method.upper(), path)
        for path, methods in app.openapi()["paths"].items()
        for method in methods
        if method.lower() in HTTP_METHODS
    ]

    assert operations, "OpenAPI route inventory must not be empty"
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
