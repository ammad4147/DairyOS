from dairyos.application.dashboard.policies.dashboard_visibility_policy import (
    DashboardVisibilityPolicy,
)

from dairyos.application.identity.models.user_role import (
    UserRole,
)



def test_owner_can_view_financials():

    policy = DashboardVisibilityPolicy()

    assert policy.can_view_financials(
        UserRole.OWNER
    )



def test_accountant_can_view_financials():

    policy = DashboardVisibilityPolicy()

    assert policy.can_view_financials(
        UserRole.ACCOUNTANT
    )



def test_milking_operator_cannot_view_financials():

    policy = DashboardVisibilityPolicy()

    assert not policy.can_view_financials(
        UserRole.MILKING_OPERATOR
    )



def test_veterinarian_can_view_health():

    policy = DashboardVisibilityPolicy()

    assert policy.can_view_health(
        UserRole.VETERINARIAN
    )
