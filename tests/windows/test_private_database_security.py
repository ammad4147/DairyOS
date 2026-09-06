import inspect

from dairyos.windows import private_database_security as security


def test_bootstrap_never_blanket_reassigns_bootstrap_role():
    source = inspect.getsource(security._bootstrap_security)

    assert "REASSIGN OWNED" not in source
    assert "_transfer_application_ownership(connection, config.user)" in source


def test_application_ownership_transfer_is_scoped_to_user_schemas():
    source = inspect.getsource(security._transfer_application_ownership)

    assert "information_schema" in source
    assert "pg_%" in source
    assert "pg_class" in source
    assert "pg_proc" in source
    assert "pg_type" in source


def test_bootstrap_role_is_never_demoted():
    source = inspect.getsource(security._bootstrap_security)

    assert "ALTER ROLE {APP_ROLE} LOGIN NOSUPERUSER" not in source
    assert "app_role = LEGACY_APP_ROLE if config.user == APP_ROLE else APP_ROLE" in source


def test_legacy_bootstrap_uses_separate_restricted_application_role():
    assert security.LEGACY_APP_ROLE != security.APP_ROLE
