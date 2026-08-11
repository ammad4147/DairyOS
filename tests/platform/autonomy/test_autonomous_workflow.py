from dairyos.platform.autonomy.orchestration.services.autonomy_orchestrator import (
    AutonomyOrchestrator,
)

from dairyos.platform.autonomy.copilot.services.farm_copilot import (
    FarmCopilot,
)

from dairyos.platform.autonomy.execution.services.execution_service import (
    ExecutionService,
)

from dairyos.platform.autonomy.learning.services.autonomy_learning_service import (
    AutonomyLearningService,
)

from dairyos.operations.execution.models.operational_execution import (
    OperationalExecution,
)


def test_autonomous_operations_pipeline():

    orchestrator = AutonomyOrchestrator()

    result = orchestrator.analyze(
        problem="Milk production decline",
        evidence=[
            "Reduced yield",
            "Health deviation",
        ],
        impact="Production loss",
        confidence=0.85,
    )

    assert result["context"].problem == (
        "Milk production decline"
    )

    assert result["recommendation"].confidence == 0.85

    copilot = FarmCopilot()

    response = copilot.respond(
        "What requires attention?",
        [
            result["recommendation"]
        ],
    )

    assert response.message

    execution = ExecutionService()

    plan = execution.create_plan(
        title="Inspect affected animals",
        description="Veterinary review",
        assigned_to="veterinarian",
        priority="high",
    )

    assert plan.status == "draft"

    execution.approve(plan)

    assert plan.status == "approved"

    operational_execution = execution.complete(
        plan,
        actor="veterinarian",
        notes="Veterinary review completed",
    )

    assert plan.status == "approved"
    assert operational_execution.status == OperationalExecution.COMPLETED
    assert execution.get_execution(plan) is operational_execution
    assert operational_execution.assigned_to == "veterinarian"

    learning = AutonomyLearningService()

    signal = learning.record(
        recommendation_id="recommendation-001",
        outcome="successful",
        confidence_change=0.05,
    )

    assert signal.outcome == "successful"
