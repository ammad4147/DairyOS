from dairyos.operations.decisions.services.decision_activation_service import (
    DecisionActivationService,
)

from dairyos.operations.decisions.services.decision_action_bridge import (
    DecisionActionBridge,
)

from dairyos.operations.decisions.services.operations_decision_service import (
    OperationsDecisionService,
)

from dairyos.operations.actions.services.operational_action_service import (
    OperationalActionService,
)

from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)

from dairyos.operations.decisions.models.decision_context import (
    DecisionContext,
)


def test_operational_decision_activates_into_execution():

    action_service = (
        OperationalActionService()
    )


    execution_service = (
        OperationalExecutionService()
    )


    decision_action_bridge = (
        DecisionActionBridge(

            action_service=action_service,

            execution_service=execution_service,

        )
    )


    activation_service = (
        DecisionActivationService(
            decision_action_bridge=decision_action_bridge
        )
    )


    decision_service = (
        OperationsDecisionService()
    )


    decision = (
        decision_service.create_decision(

            context=DecisionContext(

                source="animal:COW-001",

                category="Review low milk production",

                description=(
                    "Milk production below expected level"
                ),

                operational_impact="MEDIUM",

            ),

            priority="MEDIUM",

            owner_action_required=True,

        )
    )


    execution = (
        activation_service.activate(

            decision=decision,

            assigned_to="farm_worker",

        )
    )


    assert execution is not None


    assert execution.execution_id.startswith(
        "EXE-"
    )


    action = (
        action_service.get_actions()[0]
    )


    assert action.source_decision_id == (
        decision.decision_id
    )


    assert execution.action_id == (
        action.action_id
    )


    assert decision.source == (
        "animal:COW-001"
    )
