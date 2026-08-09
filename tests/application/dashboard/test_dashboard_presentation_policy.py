from dairyos.application.dashboard.policies.dashboard_presentation_policy import (
    DashboardPresentationPolicy,
)

from dairyos.application.dashboard.policies.dashboard_section import (
    DashboardSection,
)

from dairyos.application.identity.models.user_role import (
    UserRole,
)



def test_owner_dashboard_sections():

    policy = DashboardPresentationPolicy()

    sections = policy.sections_for(
        UserRole.OWNER
    )

    assert DashboardSection.FINANCE in sections
    assert DashboardSection.PRODUCTION in sections



def test_milking_operator_dashboard_sections():

    policy = DashboardPresentationPolicy()

    sections = policy.sections_for(
        UserRole.MILKING_OPERATOR
    )

    assert DashboardSection.MILKING in sections
    assert DashboardSection.FINANCE not in sections



def test_labourer_only_tasks():

    policy = DashboardPresentationPolicy()

    sections = policy.sections_for(
        UserRole.LABOURER
    )

    assert sections == {
        DashboardSection.TASKS
    }
