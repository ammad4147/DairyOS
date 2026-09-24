"""Regression coverage for the packaged desktop static-file boundary."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from dairyos.middleware.desktop_session import enforce_desktop_session


@pytest.mark.anyio
@pytest.mark.parametrize("path", ["/serviceWorker.js", "/manifest.json", "/dairyos-cow.svg"])
async def test_public_pwa_static_assets_are_available_in_production(monkeypatch, path):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv("DAIRYOS_RUNTIME_MODE", "development")
    request = SimpleNamespace(
        method="GET",
        url=SimpleNamespace(path=path),
        headers={},
        base_url="http://127.0.0.1:8123/",
    )
    called = False

    async def call_next(received):
        nonlocal called
        called = received is request
        return "served"

    assert await enforce_desktop_session(request, call_next) == "served"
    assert called is True


@pytest.mark.anyio
async def test_other_production_routes_still_require_desktop_session(monkeypatch):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv("DAIRYOS_RUNTIME_MODE", "development")
    request = SimpleNamespace(
        method="GET",
        url=SimpleNamespace(path="/ai-assistant/tools"),
        headers={},
        base_url="http://127.0.0.1:8123/",
    )

    async def call_next(_received):
        raise AssertionError("protected route must not reach the application")

    response = await enforce_desktop_session(request, call_next)
    assert response.status_code == 401


@pytest.mark.anyio
async def test_explicit_browser_mode_uses_human_access_gate_not_desktop_token(monkeypatch):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv("DAIRYOS_RUNTIME_MODE", "development")
    monkeypatch.setenv("DAIRYOS_BROWSER_MODE", "1")
    request = SimpleNamespace(
        method="GET",
        url=SimpleNamespace(path="/human-access/status"),
        headers={},
        base_url="http://127.0.0.1:8123/",
    )
    called = False

    async def call_next(received):
        nonlocal called
        called = received is request
        return "served by human-access gate"

    assert await enforce_desktop_session(request, call_next) == "served by human-access gate"
    assert called is True


@pytest.mark.anyio
@pytest.mark.parametrize(
    "path",
    [
        "/settings/data-management/export",
        "/settings/data-management/validate",
        "/settings/data-management/import",
    ],
)
async def test_data_management_routes_reject_non_desktop_access(monkeypatch, path):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv("DAIRYOS_RUNTIME_MODE", "development")
    monkeypatch.setenv("DAIRYOS_DESKTOP_SESSION_TOKEN", "desktop-capability")
    request = SimpleNamespace(
        method="POST",
        url=SimpleNamespace(path=path),
        headers={},
        base_url="http://127.0.0.1:8123/",
    )

    async def call_next(_received):
        raise AssertionError("data-management route must not reach the application")

    response = await enforce_desktop_session(request, call_next)
    assert response.status_code == 401
