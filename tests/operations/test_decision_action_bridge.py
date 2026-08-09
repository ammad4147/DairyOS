from dairyos.operations.actions.services.operational_action_service import (
    OperationalActionService,
)

from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)

from dairyos.operations.decisions.services.decision_action_bridge import (
    DecisionActionBridge,
)


class FakePriority:

    level = "HIGH"



class FakeDecision:

    decision_id = "DEC-0001"

    title = "Health Alert Follow Up"

    description = "Inspect affected animal"

    priority = FakePriority()



def test_decision_creates_execution():

    action_service = OperationalActionService()

    execution_service = OperationalExecutionService()


    bridge = DecisionActionBridge(

        action_service,

        execution_service,

    )


    execution = bridge.create_execution_from_decision(

        FakeDecision(),

        "Farm Supervisor",

    )


    assert execution.action_id == "ACT-0001"

    assert execution.assigned_to == "Farm Supervisor"

    assert execution.status == "CREATED"
