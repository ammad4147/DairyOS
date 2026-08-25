"""Tests for PostgreSQL Windows Service discovery and startup policy."""

from __future__ import annotations

from types import SimpleNamespace

from dairyos.windows import postgres_service


def test_list_postgresql_services_parses_sc_output(monkeypatch):
    output = """
SERVICE_NAME: PostgreSQL-x64-15
        STATE              : 1  STOPPED
SERVICE_NAME: postgresql-x64-17
        STATE              : 4  RUNNING
SERVICE_NAME: OtherService
        STATE              : 4  RUNNING
"""

    monkeypatch.setattr(
        postgres_service,
        "_run_sc",
        lambda *args: SimpleNamespace(returncode=0, stdout=output, stderr=""),
    )
    monkeypatch.setattr(postgres_service.os, "name", "nt")

    assert postgres_service.list_postgresql_services() == [
        "postgresql-x64-17",
        "PostgreSQL-x64-15",
    ]


def test_configured_service_name_wins(monkeypatch):
    monkeypatch.setenv("DAIRYOS_POSTGRES_SERVICE", "postgresql-x64-16")
    assert postgres_service.configured_service_name() == "postgresql-x64-16"


def test_resolve_service_name_requires_installed_service(monkeypatch):
    monkeypatch.delenv("DAIRYOS_POSTGRES_SERVICE", raising=False)
    monkeypatch.setattr(postgres_service.os, "name", "nt")
    monkeypatch.setattr(postgres_service, "list_postgresql_services", lambda: [])

    try:
        postgres_service.resolve_service_name()
    except postgres_service.PostgreSQLServiceError as exc:
        assert "No PostgreSQL Windows Service was found" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("resolve_service_name unexpectedly succeeded")


def test_ensure_postgresql_running_does_not_start_running_service(monkeypatch):
    monkeypatch.setattr(postgres_service.os, "name", "nt")
    monkeypatch.setenv("DAIRYOS_POSTGRES_SERVICE", "postgresql-x64-17")
    monkeypatch.setattr(postgres_service, "service_is_running", lambda name: True)

    calls = []
    monkeypatch.setattr(postgres_service, "_run_sc", lambda *args: calls.append(args))

    assert postgres_service.ensure_postgresql_running() == "postgresql-x64-17"
    assert calls == []
