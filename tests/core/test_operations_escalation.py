from datetime import datetime


from dairyos.operations.escalation.models.escalation_level import (
    EscalationLevel,
)

from dairyos.operations.escalation.models.operational_escalation import (
    OperationalEscalation,
)

from dairyos.operations.escalation.services.escalation_rule_service import (
    EscalationRuleService,
)

from dairyos.operations.escalation.services.escalation_management_service import (
    EscalationManagementService,
)



def test_escalation_level_detection():

    service = EscalationRuleService()

    level = service.determine_level(10)

    assert level == "LEVEL_TWO"



def test_create_escalation():

    service = EscalationManagementService()

    escalation = OperationalEscalation(
        escalation_id="ESC-001",
        issue_reference="TASK-001",
        level=EscalationLevel.LEVEL_ONE,
        assigned_to="Supervisor",
        created_at=datetime.now(),
    )

    service.create_escalation(escalation)

    assert len(service.active_escalations()) == 1
