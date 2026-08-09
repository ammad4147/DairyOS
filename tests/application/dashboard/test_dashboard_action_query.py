from uuid import uuid4

from dairyos.application.dashboard.services.dashboard_query_service import (
    DashboardQueryService,
)

from dairyos.application.dashboard.services.farm_dashboard_service import (
    FarmDashboardService,
)

from dairyos.application.identity.models.operational_user import (
    OperationalUser,
)

from dairyos.application.identity.models.user_role import (
    UserRole,
)

from dairyos.application.identity.repositories.adapters.memory_user_repository import (
    MemoryUserRepository,
)

from dairyos.application.identity.services.identity_service import (
    IdentityService,
)



def test_dashboard_query_returns_role_actions():

    identity = IdentityService(
        MemoryUserRepository()
    )


    dashboard = DashboardQueryService(
        identity,
        FarmDashboardService(),
    )


    user = OperationalUser(
        user_id=uuid4(),
        name="Operator",
        role=UserRole.MILKING_OPERATOR,
    )


    identity.register_user(
        user
    )


    actions = dashboard.get_dashboard_actions(
        user
    )


    assert len(actions) > 0

    assert (
        actions[0]
        .responsible_role
        ==
        UserRole.MILKING_OPERATOR.value
    )
