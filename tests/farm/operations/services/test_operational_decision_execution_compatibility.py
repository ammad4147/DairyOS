from dairyos.farm.operations.models.operational_decision import (
    OperationalDecision,
)

from dairyos.farm.operations.runtime.farm_operations_runtime import (
    FarmOperationsRuntime,
)

from dairyos.farm.operations.services.operational_decision_execution_boundary import (
    OperationalDecisionExecutionBoundary,
)


def test_operational_decision_requires_controlled_execution_boundary():

    decision = OperationalDecision(
        type="health",
        priority="high",
        action="review_health_observation",
        title="Review health observation",
        source="health",
        escalation_level="HIGH",
        details={
            "animal_id": "COW-001",
        },
    )

    runtime = FarmOperationsRuntime()

    boundary = OperationalDecisionExecutionBoundary(
        runtime
    )

    execution = boundary.execute(
        decision,
        approved_by="farm_manager",
    )

    assert execution.decision_id == (
        decision.decision_id
    )

    assert execution.status == (
        "REJECTED"
    )



def test_supported_decision_execution_does_not_modify_decision():

    decision = OperationalDecision(
        type="production",
        priority="high",
        action="record_milk_activity",
        title="Record milk production",
        source="production",
        escalation_level="HIGH",
        details={
            "animal_id": "COW-001",
            "session": "MORNING",
            "litres": 20,
        },
    )

    original_action = decision.action

    runtime = FarmOperationsRuntime()

    boundary = OperationalDecisionExecutionBoundary(
        runtime
    )

    execution = boundary.execute(
        decision,
        approved_by="farm_manager",
    )

    assert decision.action == original_action

    assert execution.action == (
        "record_milk_activity"
    )

    assert execution.status == (
        "EXECUTED"
    )
