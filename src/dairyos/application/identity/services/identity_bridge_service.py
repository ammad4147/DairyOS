from uuid import UUID

from ..models.operational_user import OperationalUser
from ..models.user_role import UserRole


class IdentityBridgeService:
    """
    Converts identity information into
    operational farm user context.

    Authentication and database identity
    remain outside this service.

    This service creates the boundary between:

    core identity
        |
        v
    application operational identity
    """


    def from_identity(
        self,
        user_id: UUID,
        username: str,
        role: str,
        active: bool = True,
    ) -> OperationalUser:
        """
        Build operational user context.
        """


        return OperationalUser(

            user_id=user_id,

            name=username,

            role=self._resolve_role(
                role
            ),

            active=active,

        )


    def _resolve_role(
        self,
        role: str,
    ) -> UserRole:
        """
        Convert stored role value
        into operational role enum.
        """

        if isinstance(
            role,
            UserRole
        ):

            return role


        return UserRole(
            role.lower()
        )
