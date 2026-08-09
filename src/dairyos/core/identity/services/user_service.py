"""
DairyOS User Service

CORE-003
"""

from ..models.identity_user import IdentityUser
from ...security.password import hash_password


def create_user(
    username: str,
    password: str
):

    return IdentityUser(
        username=username,
        password_hash=hash_password(password),
        active=True
    )