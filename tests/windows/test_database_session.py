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
        raise AssertionError(
            "non-local production database must require explicit credentials"
        )


def test_explicit_non_local_passwordless_production_url_is_rejected(monkeypatch):
    session = importlib.import_module("dairyos.data.database.session")
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv(
        "DAIRYOS_DATABASE_URL",
        "postgresql+psycopg://dairyos@db.example.invalid:5432/dairyos",
    )

    try:
        session._build_database_url()
    except RuntimeError as exc:
        assert "DAIRYOS_DATABASE_URL" in str(exc)
    else:
        raise AssertionError(
            "passwordless explicit remote production URL must be rejected"
        )


def test_explicit_local_passwordless_production_url_is_allowed(monkeypatch):
    session = importlib.import_module("dairyos.data.database.session")
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv(
        "DAIRYOS_DATABASE_URL",
        "postgresql+psycopg://dairyos@127.0.0.1:5432/dairyos",
    )

    assert session._build_database_url().endswith("/dairyos")


def test_passwordless_loopback_allows_explicit_disposable_test_database(monkeypatch):
    session = importlib.import_module("dairyos.data.database.session")
    monkeypatch.delenv("DAIRYOS_DATABASE_URL", raising=False)
    monkeypatch.delenv("DAIRYOS_DB_PASSWORD", raising=False)
    monkeypatch.setenv("DAIRYOS_DB_NAME", "dairyos_test_ai_assistant")
    monkeypatch.setenv("DAIRYOS_DB_USER", "dairyos")
    monkeypatch.setenv("DAIRYOS_DB_HOST", "127.0.0.1")
    assert "dairyos_test_ai_assistant" in session._build_database_url()


def test_passwordless_non_test_database_still_requires_production_secret(monkeypatch):
    session = importlib.import_module("dairyos.data.database.session")
    monkeypatch.delenv("DAIRYOS_DATABASE_URL", raising=False)
    monkeypatch.delenv("DAIRYOS_DB_PASSWORD", raising=False)
    monkeypatch.setenv("DAIRYOS_DB_NAME", "farm_backup")
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    try:
        session._build_database_url()
    except RuntimeError as exc:
        assert "DAIRYOS_DB_PASSWORD" in str(exc)
    else:  # pragma: no cover - assertion documents the security contract
        raise AssertionError(
            "non-test production database accepted passwordless access"
        )
