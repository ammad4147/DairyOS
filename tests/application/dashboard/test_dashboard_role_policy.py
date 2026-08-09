from uuid import uuid4

from dairyos.application.dashboard.policies.dashboard_role_policy import (
    DashboardRolePolicy,
)

from dairyos.application.dashboard.policies.dashboard_section import (
    DashboardSection,
)

from dairyos.application.identity.models.user_role import (
    UserRole,
)


def test_owner_dashboard_profile():

    profile = DashboardRolePolicy().profile_for(
        UserRole.OWNER
    )

    assert DashboardSection.FINANCE in profile.sections
    assert DashboardSection.HERD in profile.sections
    assert "revenue" in profile.priority_metrics



def test_milking_operator_dashboard_profile():

    profile = DashboardRolePolicy().profile_for(
        UserRole.MILKING_OPERATOR
    )

    assert DashboardSection.MILKING in profile.sections
    assert DashboardSection.FINANCE not in profile.sections
    assert "milk_total" in profile.priority_metrics



def test_feed_supervisor_dashboard_profile():

    profile = DashboardRolePolicy().profile_for(
        UserRole.FEED_SUPERVISOR
    )

    assert DashboardSection.FEED in profile.sections
    assert "feed_consumption" in profile.priority_metrics



def test_accountant_dashboard_profile():

    profile = DashboardRolePolicy().profile_for(
        UserRole.ACCOUNTANT
    )

    assert DashboardSection.FINANCE in profile.sections
    assert DashboardSection.HERD not in profile.sections



def test_veterinarian_dashboard_profile():

    profile = DashboardRolePolicy().profile_for(
        UserRole.VETERINARIAN
    )

    assert DashboardSection.HEALTH in profile.sections
    assert DashboardSection.HERD in profile.sections
