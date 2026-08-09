from dairyos.operations.governance.models.governance_rule import GovernanceRule
from dairyos.operations.governance.services.governance_service import (
    GovernanceService,
)

from dairyos.operations.governance.models.escalation_policy import (
    EscalationPolicy,
)

from dairyos.operations.governance.services.escalation_service import (
    EscalationService,
)


def test_governance_rule_registration():

    service = GovernanceService()

    service.register_rule(
        GovernanceRule(
            rule_id="RULE-001",
            title="Daily milk review",
            category="Production",
            owner_role="Farm Manager",
            frequency="Daily",
            escalation_required=True,
        )
    )

    assert len(service.get_rules()) == 1


def test_escalation_policy():

    service = EscalationService()

    service.register_policy(
        EscalationPolicy(
            policy_id="ESC-001",
            issue_category="Feeding",
            escalation_level=1,
            responsible_role="Supervisor",
            response_time_hours=24,
        )
    )

    assert service.get_policies()[0].escalation_level == 1
