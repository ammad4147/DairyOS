from enum import Enum


class AuthorizationRole(str, Enum):
    """Farm-scoped authorization roles for DairyOS."""

    OWNER = "owner"
    MANAGER = "manager"
    MILKER = "milker"
