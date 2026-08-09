from uuid import UUID

from ..models.operational_user import OperationalUser

from ..models.user_role import UserRole

from ..services.identity_bridge_service import (
    IdentityBridgeService,
)

from dairyos.application.dashboard.context.dashboard_context import (
    DashboardContext,
)


class IdentityContextService:
    """
    Creates operational application context.

    Converts identity information into
    contexts consumed by application services.

    This keeps identity resolution outside
    individual modules.
    """


    def __init__(
        self,
        bridge: IdentityBridgeService | None = None,
    ):

        self.bridge = (
            bridge
            if bridge
            else IdentityBridgeService()
        )


    def create_user_context(
        self,
        user_id: UUID,
        username: str,
        role: str | UserRole,
        active: bool = True,
    ) -> OperationalUser:

        return self.bridge.from_identity(
            user_id=user_id,
            username=username,
            role=role,
            active=active,
        )


    def create_dashboard_context(
        self,
        user: OperationalUser,
    ) -> DashboardContext:

        return DashboardContext(

            user_id=user.user_id,

            user_name=user.name,

            role=user.role,

        )
