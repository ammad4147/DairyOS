from uuid import UUID

from ..models.operational_user import OperationalUser
from ..policies.permission import Permission
from ..policies.role_permission_policy import RolePermissionPolicy
from ..repositories.user_repository import UserRepository


class IdentityService:
    """
    Operational identity management service.

    Handles farm user responsibility context.
    Authentication remains outside this layer.
    """

    def __init__(
        self,
        repository: UserRepository,
        permission_policy: RolePermissionPolicy | None = None
    ):

        self.repository = repository

        self.permission_policy = (
            permission_policy
            if permission_policy
            else RolePermissionPolicy()
        )


    def register_user(
        self,
        user: OperationalUser
    ) -> OperationalUser:

        return self.repository.save(user)


    def get_user(
        self,
        user_id: UUID
    ):

        return self.repository.get(user_id)


    def get_users(self):

        return self.repository.list_all()


    def can_access(
        self,
        user: OperationalUser,
        permission: Permission
    ) -> bool:

        if not user.active:
            return False

        return self.permission_policy.can(
            user.role,
            permission
        )


    def get_permissions(
        self,
        user: OperationalUser
    ) -> set[Permission]:

        if not user.active:
            return set()

        return self.permission_policy.permissions_for(
            user.role
        )
