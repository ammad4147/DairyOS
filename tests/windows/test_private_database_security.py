import inspect

from dairyos.windows import private_database_security as security


def test_bootstrap_never_blanket_reassigns_bootstrap_role():
    source = inspect.getsource(security._bootstrap_security)

    assert "REASSIGN OWNED" not in source
    assert "_transfer_application_ownership(connection)" in source


def test_application_ownership_transfer_is_scoped_to_user_schemas():
    source = inspect.getsource(security._transfer_application_ownership)

    assert "information_schema" in source
    assert "pg_%" in source
    assert "pg_class" in source
    assert "pg_proc" in source
    assert "pg_type" in source
