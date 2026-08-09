from dairyos.operations.executive_decision.services.executive_decision_service import (
    ExecutiveDecisionService,
)

from dairyos.operations.command_integration.services.operations_command_adapter import (
    OperationsCommandAdapter,
)

from dairyos.operations.command_integration.services.command_routing_service import (
    CommandRoutingService,
)

from dairyos.operations.command_integration.models.command_priority import (
    CommandPriority,
)



def test_command_creation_from_decision():

    decision_service = ExecutiveDecisionService()

    decision = decision_service.create_decision(
        "DEC-100",
        "Animal Health Risk",
        20,
    )


    adapter = OperationsCommandAdapter()


    command = adapter.create_command(
        "CMD-100",
        "Health Intervention",
        decision,
    )


    assert command.priority == CommandPriority.CRITICAL



def test_command_routing_attention():

    decision_service = ExecutiveDecisionService()

    decision = decision_service.create_decision(
        "DEC-101",
        "Feed Review",
        50,
    )


    adapter = OperationsCommandAdapter()

    command = adapter.create_command(
        "CMD-101",
        "Feed Investigation",
        decision,
    )


    router = CommandRoutingService()


    assert router.requires_immediate_attention(command) is True
