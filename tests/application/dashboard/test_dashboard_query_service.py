from uuid import uuid4

import pytest

from dairyos.application.dashboard.context.dashboard_context import (
    DashboardContext,
)

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



def test_dashboard_query_allows_authorized_user():

    identity = IdentityService(
        MemoryUserRepository()
    )

    dashboard = DashboardQueryService(
        identity,
        FarmDashboardService(),
    )


    user = OperationalUser(
        user_id=uuid4(),
        name="Ahmed",
        role=UserRole.MILKING_OPERATOR,
    )


    identity.register_user(user)


    context = DashboardContext(
        user_id=user.user_id,
        user_name=user.name,
        role=user.role,
    )


    result = dashboard.get_dashboard(
        user,
        context,
    )


    assert result is not None



def test_dashboard_query_blocks_inactive_user():

    identity = IdentityService(
        MemoryUserRepository()
    )

    dashboard = DashboardQueryService(
        identity,
        FarmDashboardService(),
    )


    user = OperationalUser(
        user_id=uuid4(),
        name="Ahmed",
        role=UserRole.MILKING_OPERATOR,
        active=False,
    )


    context = DashboardContext(
        user_id=user.user_id,
        user_name=user.name,
        role=user.role,
    )


    with pytest.raises(PermissionError):

        dashboard.get_dashboard(
            user,
            context,
        )
