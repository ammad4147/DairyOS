"""
DairyOS Permission Engine

CORE-003
"""


ROLE_PERMISSIONS = {

    "OWNER": [
        "VIEW_ALL",
        "MANAGE_FINANCE",
        "MANAGE_USERS"
    ],

    "FARM_MANAGER": [
        "VIEW_OPERATIONS",
        "MANAGE_TASKS"
    ],

    "VETERINARIAN": [
        "VIEW_ANIMALS",
        "MANAGE_HEALTH"
    ],

    "WORKER": [
        "VIEW_TASKS"
    ]
}


def has_permission(
    role: str,
    permission: str
) -> bool:

    permissions = ROLE_PERMISSIONS.get(
        role,
        []
    )

    return permission in permissions