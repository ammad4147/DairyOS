"""Regression coverage for the packaged desktop static-file boundary."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from dairyos.middleware.desktop_session import enforce_desktop_session


@pytest.mark.anyio
@pytest.mark.parametrize("path", ["/serviceWorker.js", "/manifest.json", "/dairyos-cow.svg"])
async def test_public_pwa_static_assets_are_available_in_production(monkeypatch, path):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
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
