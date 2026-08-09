from dairyos.operations.automation.models.automation_rule import (
    AutomationRule,
)

from dairyos.operations.automation.services.automation_rule_service import (
    AutomationRuleService,
)

from dairyos.operations.automation.services.automation_execution_service import (
    AutomationExecutionService,
)


def test_automation_rule_registration():

    service = AutomationRuleService()

    service.register_rule(
        AutomationRule(
            rule_id="RULE-001",
            name="Overdue Feeding",
            trigger="FEED_DELAY",
            action="CREATE_ALERT",
        )
    )

    assert len(service.active_rules()) == 1



def test_automation_execution():

    service = AutomationExecutionService()

    event = service.execute(
        "FEED_DELAY",
    )

    assert event.executed is True
