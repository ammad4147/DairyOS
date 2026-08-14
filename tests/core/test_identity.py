from dairyos.core.security.password import (
    hash_password,
    verify_password
)


def test_password_security():

    password = "DairyOS123"

    hashed = hash_password(password)

    assert verify_password(
        password,
        hashed
    )
