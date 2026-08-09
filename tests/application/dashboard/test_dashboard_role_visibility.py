from dairyos.application.dashboard.policies.dashboard_visibility_policy import (
    DashboardVisibilityPolicy,
)

from dairyos.application.dashboard.policies.dashboard_section import (
    DashboardSection,
)

from dairyos.application.identity.models.user_role import (
    UserRole,
)



def test_owner_can_view_finance_section():

    policy = DashboardVisibilityPolicy()

    sections = policy.sections_for(
        UserRole.OWNER
    )

    assert DashboardSection.FINANCE in sections



def test_accountant_can_view_finance():

    policy = DashboardVisibilityPolicy()

    sections = policy.sections_for(
        UserRole.ACCOUNTANT
    )

    assert DashboardSection.FINANCE in sections



def test_accountant_cannot_view_health():

    policy = DashboardVisibilityPolicy()

    sections = policy.sections_for(
        UserRole.ACCOUNTANT
    )

    assert DashboardSection.HEALTH not in sections



def test_milking_operator_can_view_milking():

    policy = DashboardVisibilityPolicy()

    sections = policy.sections_for(
        UserRole.MILKING_OPERATOR
    )

    assert DashboardSection.MILKING in sections



def test_milking_operator_cannot_view_finance():

    policy = DashboardVisibilityPolicy()

    sections = policy.sections_for(
        UserRole.MILKING_OPERATOR
    )

    assert DashboardSection.FINANCE not in sections



def test_veterinarian_can_view_health():

    policy = DashboardVisibilityPolicy()

    sections = policy.sections_for(
        UserRole.VETERINARIAN
    )

    assert DashboardSection.HEALTH in sections



def test_labourer_has_basic_operational_view():

    policy = DashboardVisibilityPolicy()

    sections = policy.sections_for(
        UserRole.LABOURER
    )

    assert DashboardSection.OPERATIONS in sections

    assert DashboardSection.FINANCE not in sections
