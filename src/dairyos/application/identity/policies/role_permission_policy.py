from dairyos.application.identity.models.user_role import UserRole
from dairyos.application.identity.policies.permission import Permission
from dairyos.application.identity.policies.role_permission import ROLE_PERMISSIONS


class RolePermissionPolicy:
    """
    Determines operational permissions
    based on farm role.
    """


    def can(
        self,
        role: UserRole,
        permission: Permission
    ) -> bool:

        return permission in ROLE_PERMISSIONS.get(
            role,
            set()
        )


    def permissions_for(
        self,
        role: UserRole
    ) -> set[Permission]:

        return ROLE_PERMISSIONS.get(
            role,
            set()
        )
