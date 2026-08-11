from dairyos.operations.execution.models.operational_execution import (
    OperationalExecution,
)

from dairyos.platform.autonomy.execution.services.execution_service import (
    ExecutionService,
)


def test_action_plan_approval_creates_canonical_execution_boundary():
    service = ExecutionService()

    plan = service.create_plan(
        title="Inspect affected animals",
        description="Veterinary review",
        assigned_to="veterinarian",
        priority="high",
    )

    assert plan.status == service.PLAN_DRAFT

    service.approve(plan)

    assert plan.status == service.PLAN_APPROVED

    execution = service.get_execution(plan)

    assert execution is not None
    assert isinstance(execution, OperationalExecution)
    assert execution.action_id.startswith("AUTONOMY-ACTION-")
    assert execution.assigned_to == "veterinarian"
    assert execution.status == execution.ASSIGNED


def test_action_plan_does_not_own_operational_execution_lifecycle():
    service = ExecutionService()

    plan = service.create_plan(
        title="Review health conditions",
        description="Inspect affected animals",
        assigned_to="veterinarian",
        priority="high",
    )

    service.approve(plan)

    assert not hasattr(plan, "start")
    assert not hasattr(plan, "complete")
    assert not hasattr(plan, "verify")
    assert not hasattr(plan, "close")

    execution = service.get_execution(plan)

    assert execution is not None
    assert execution.status == execution.ASSIGNED


def test_action_plan_completion_returns_canonical_execution():
    service = ExecutionService()

    plan = service.create_plan(
        title="Complete veterinary inspection",
        description="Inspect affected animals",
        assigned_to="veterinarian",
        priority="high",
    )

    service.approve(plan)

    execution = service.complete(
        plan,
        notes="Inspection completed",
        actor="veterinarian",
    )

    assert isinstance(execution, OperationalExecution)
    assert execution.status == execution.COMPLETED
    assert execution.completed_by == "veterinarian"
    assert execution.completed_at is not None
    assert execution.notes == "Inspection completed"

    # The plan remains a planning/approval artifact.
    assert plan.status == service.PLAN_APPROVED
