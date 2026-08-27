import importlib


def test_local_dairyos_role_can_build_passwordless_production_url(monkeypatch):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.delenv("DAIRYOS_DATABASE_URL", raising=False)
    monkeypatch.setenv("DAIRYOS_DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DAIRYOS_DB_PORT", "5432")
    monkeypatch.setenv("DAIRYOS_DB_NAME", "dairyos")
    monkeypatch.setenv("DAIRYOS_DB_USER", "dairyos")
    monkeypatch.delenv("DAIRYOS_DB_PASSWORD", raising=False)

    session = importlib.import_module("dairyos.data.database.session")
    url = session._build_database_url()

    assert url == "postgresql+psycopg://dairyos@127.0.0.1:5432/dairyos"


def test_non_local_production_still_requires_database_password(monkeypatch):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.delenv("DAIRYOS_DATABASE_URL", raising=False)
    monkeypatch.setenv("DAIRYOS_DB_HOST", "db.example.invalid")
    monkeypatch.setenv("DAIRYOS_DB_PORT", "5432")
    monkeypatch.setenv("DAIRYOS_DB_NAME", "dairyos")
    monkeypatch.setenv("DAIRYOS_DB_USER", "dairyos")
    monkeypatch.delenv("DAIRYOS_DB_PASSWORD", raising=False)

    session = importlib.import_module("dairyos.data.database.session")

    try:
        session._build_database_url()
    except RuntimeError as exc:
        assert "DAIRYOS_DB_PASSWORD" in str(exc)
    else:
        raise AssertionError("non-local production database must require explicit credentials")
