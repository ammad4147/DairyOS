from __future__ import annotations

import json

import pytest

from dairyos.windows import system_postgres_admin as admin


class _Cursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement):
        assert statement == "SELECT 1"

    def fetchone(self):
        return (1,)


class _Connection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return _Cursor()


def _configure(monkeypatch, tmp_path):
    monkeypatch.setenv("DAIRYOS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DAIRYOS_DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DAIRYOS_DB_PORT", "5432")
    monkeypatch.setenv("DAIRYOS_DB_NAME", "dairyos")
    monkeypatch.delenv(admin.MIGRATION_DATABASE_URL_ENV, raising=False)
    monkeypatch.setattr(
        admin,
        "_protect",
        lambda value: {"scheme": "test", "value": f"protected:{value}"},
    )
    monkeypatch.setattr(
        admin,
        "_unprotect",
        lambda payload: str(payload["value"]).removeprefix("protected:"),
    )


def test_adoption_validates_then_stores_only_protected_material(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    calls = []

    def connect(**kwargs):
        calls.append(kwargs)
        return _Connection()

    monkeypatch.setattr(admin.psycopg, "connect", connect)

    path = admin.adopt_admin_password("admin-secret")

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert calls[0]["user"] == "dairyos_admin"
    assert calls[0]["password"] == "admin-secret"
    assert payload["role"] == "dairyos_admin"
    assert payload["password"] == {"scheme": "test", "value": "protected:admin-secret"}
    assert "admin-secret" not in path.read_text(encoding="utf-8").replace(
        "protected:admin-secret", ""
    )


def test_invalid_password_is_rejected_without_persisting(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)

    def reject(**_kwargs):
        raise RuntimeError("authentication failed")

    monkeypatch.setattr(admin.psycopg, "connect", reject)

    with pytest.raises(
        admin.SystemPostgresAdminCredentialError,
        match="could not be validated",
    ):
        admin.adopt_admin_password("wrong")

    assert not admin.credential_state_path().exists()


def test_staged_url_uses_adopted_admin_and_is_not_plaintext_storage(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    monkeypatch.setattr(admin.psycopg, "connect", lambda **_kwargs: _Connection())

    admin.adopt_admin_password("p@ss/word")
    admin.stage_migration_database_url()

    url = admin.os.environ[admin.MIGRATION_DATABASE_URL_ENV]
    assert url.startswith("postgresql+psycopg://dairyos_admin:")
    assert "p%40ss%2Fword" in url
    assert url.endswith("@127.0.0.1:5432/dairyos")


def test_corrupt_credential_requires_repair(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    path = admin.credential_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(
        admin.SystemPostgresAdminCredentialError,
        match="unreadable and must be repaired",
    ):
        admin.migration_database_url()


def test_credential_for_different_database_requires_repair(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    monkeypatch.setattr(admin.psycopg, "connect", lambda **_kwargs: _Connection())
    admin.adopt_admin_password("admin-secret")

    monkeypatch.setenv("DAIRYOS_DB_PORT", "55432")

    with pytest.raises(
        admin.SystemPostgresAdminCredentialError,
        match="different system PostgreSQL instance",
    ):
        admin.migration_database_url()


def test_existing_privileged_url_is_not_overwritten(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    monkeypatch.setenv(admin.MIGRATION_DATABASE_URL_ENV, "postgresql+psycopg://private-admin")

    admin.stage_migration_database_url()

    assert admin.os.environ[admin.MIGRATION_DATABASE_URL_ENV] == "postgresql+psycopg://private-admin"


@pytest.mark.skipif(admin.os.name != "nt", reason="Windows DPAPI contract")
def test_windows_dpapi_round_trip_uses_user_protection():
    payload = admin._protect("dpapi-round-trip-secret")

    assert payload["scheme"] == "windows-dpapi-user"
    assert payload["value"] != "dpapi-round-trip-secret"
    assert admin._unprotect(payload) == "dpapi-round-trip-secret"
