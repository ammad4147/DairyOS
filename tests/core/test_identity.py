from dairyos.core.security.password import (
    hash_password,
    verify_password
)

from dairyos.core.security.permissions import (
    has_permission
)


def test_password_security():

    password = "DairyOS123"

    hashed = hash_password(password)

    assert verify_password(
        password,
        hashed
    )


def test_owner_permission():

    assert has_permission(
        "OWNER",
        "MANAGE_FINANCE"
    )