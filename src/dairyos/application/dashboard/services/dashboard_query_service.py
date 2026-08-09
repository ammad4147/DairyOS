from dairyos.application.dashboard.context.dashboard_context import (
    DashboardContext,
)

from dairyos.application.dashboard.models.farm_today import (
    FarmTodaySnapshot,
)

from dairyos.application.dashboard.models.dashboard_role_profile import (
    DashboardRoleProfile,
)

from dairyos.application.dashboard.models.dashboard_action import (
    DashboardAction,
)

from dairyos.application.dashboard.policies.dashboard_role_policy import (
    DashboardRolePolicy,
)

from dairyos.application.dashboard.policies.dashboard_section import (
    DashboardSection,
)

from dairyos.application.dashboard.policies.dashboard_visibility_policy import (
    DashboardVisibilityPolicy,
)

from dairyos.application.dashboard.policies.dashboard_responsibility_policy import (
    DashboardResponsibilityPolicy,
)

from dairyos.application.dashboard.services.farm_dashboard_service import (
    FarmDashboardService,
)

from dairyos.application.identity.services.identity_service import (
    IdentityService,
)

from dairyos.application.identity.models.operational_user import (
    OperationalUser,
)

from dairyos.application.identity.policies.permission import (
    Permission,
)


class DashboardQueryService:
    """
    Application query boundary for dashboards.

    Responsible for:

    - validating dashboard access
    - resolving user context
    - resolving dashboard visibility
    - resolving dashboard experience
    - resolving operational responsibilities
    - returning dashboard read models

    Does not own dashboard calculations.
    """


    def __init__(
        self,
        identity_service: IdentityService,
        dashboard_service: FarmDashboardService,
        visibility_policy: DashboardVisibilityPolicy | None = None,
        role_policy: DashboardRolePolicy | None = None,
        responsibility_policy: DashboardResponsibilityPolicy | None = None,
    ):

        self.identity_service = identity_service

        self.dashboard_service = dashboard_service

        self.visibility_policy = (
            visibility_policy
            if visibility_policy
            else DashboardVisibilityPolicy()
        )

        self.role_policy = (
            role_policy
            if role_policy
            else DashboardRolePolicy()
        )

        self.responsibility_policy = (
            responsibility_policy
            if responsibility_policy
            else DashboardResponsibilityPolicy()
        )



    def get_dashboard(
        self,
        user: OperationalUser,
        context: DashboardContext,
    ) -> FarmTodaySnapshot:


        if not self.identity_service.can_access(
            user,
            Permission.VIEW_DASHBOARD,
        ):

            raise PermissionError(
                "User does not have dashboard access"
            )


        return (
            self.dashboard_service
            .get_today(
                context
            )
        )



    def get_visible_sections(
        self,
        user: OperationalUser,
    ) -> set[DashboardSection]:


        if not user.active:

            return set()


        return (
            self.visibility_policy
            .sections_for(
                user.role
            )
        )



    def get_dashboard_profile(
        self,
        user: OperationalUser,
    ) -> DashboardRoleProfile:


        if not user.active:

            raise PermissionError(
                "Inactive user has no dashboard profile"
            )


        return (
            self.role_policy
            .profile_for(
                user.role
            )
        )



    def get_dashboard_actions(
        self,
        user: OperationalUser,
    ) -> list[DashboardAction]:


        if not user.active:

            return []


        return (
            self.responsibility_policy
            .actions_for(
                user.role
            )
        )
