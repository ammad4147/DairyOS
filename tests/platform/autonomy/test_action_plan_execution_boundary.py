from dairyos.platform.autonomy.execution.models.action_plan import ActionPlan
from dairyos.platform.autonomy.execution.services.execution_service import ExecutionService
from dairyos.operations.execution.models.operational_execution import OperationalExecution


def test_action_plan_accepts_only_planning_states():
    valid_states = {
        "draft",
        "pending_approval",
        "approved",
        "rejected",
    }

    for status in valid_states:
        plan = ActionPlan(
            title="Test action",
            description="Test description",
            assigned_to="operator",
            priority="high",
            status=status,
        )

        assert plan.status == status


def test_action_plan_rejects_operational_execution_states():
    operational_states = {
        OperationalExecution.CREATED,
        OperationalExecution.ASSIGNED,
        OperationalExecution.ACKNOWLEDGED,
        OperationalExecution.STARTED,
        OperationalExecution.COMPLETED,
        OperationalExecution.VERIFIED,
        OperationalExecution.CLOSED,
    }

    for status in operational_states:
        try:
            ActionPlan(
                title="Test action",
                description="Test description",
                assigned_to="operator",
                priority="high",
                status=status,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"ActionPlan incorrectly accepted execution state {status!r}"
            )


def test_autonomy_completion_changes_only_canonical_execution():
    service = ExecutionService()

    plan = service.create_plan(
        title="Inspect animals",
        description="Veterinary inspection",
        assigned_to="veterinarian",
        priority="high",
    )

    service.approve(plan)

    execution = service.complete(
        plan,
        actor="veterinarian",
        notes="Inspection completed",
    )

    assert plan.status == "approved"
    assert execution.status == OperationalExecution.COMPLETED
    assert service.get_execution(plan) is execution


def test_autonomy_completion_is_idempotent_on_canonical_execution():
    service = ExecutionService()

    plan = service.create_plan(
        title="Inspect animals",
        description="Veterinary inspection",
        assigned_to="veterinarian",
        priority="high",
    )

    service.approve(plan)

    first = service.complete(plan)
    second = service.complete(plan)

    assert plan.status == "approved"
    assert first is second
    assert second.status == OperationalExecution.COMPLETED
