from dairyos.application.dashboard.policies.dashboard_responsibility_policy import (
    DashboardResponsibilityPolicy,
)

from dairyos.application.identity.models.user_role import (
    UserRole,
)


def test_owner_has_operational_review_actions():

    actions = DashboardResponsibilityPolicy().actions_for(
        UserRole.OWNER
    )

    assert len(actions) > 0

    assert (
        actions[0]
        .responsible_role
        == UserRole.OWNER.value
    )



def test_milking_operator_has_milking_action():

    actions = DashboardResponsibilityPolicy().actions_for(
        UserRole.MILKING_OPERATOR
    )

    assert any(
        action.action_type == "milk_recording"
        for action in actions
    )



def test_feed_supervisor_has_feed_action():

    actions = DashboardResponsibilityPolicy().actions_for(
        UserRole.FEED_SUPERVISOR
    )

    assert any(
        action.action_type == "feed_recording"
        for action in actions
    )



def test_veterinarian_has_health_action():

    actions = DashboardResponsibilityPolicy().actions_for(
        UserRole.VETERINARIAN
    )

    assert any(
        action.action_type == "health_recording"
        for action in actions
    )



def test_accountant_has_finance_action():

    actions = DashboardResponsibilityPolicy().actions_for(
        UserRole.ACCOUNTANT
    )

    assert any(
        action.action_type == "financial_review"
        for action in actions
    )
