from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)


def test_execution_ids_are_unique_across_service_instances():
    first = OperationalExecutionService()
    second = OperationalExecutionService()

    execution_a = first.create_execution(
        action_id="ACTION-A",
        assigned_to="tester",
    )

    execution_b = second.create_execution(
        action_id="ACTION-B",
        assigned_to="tester",
    )

    assert execution_a.execution_id != execution_b.execution_id
    assert execution_a.execution_id.startswith("EXE-")
    assert execution_b.execution_id.startswith("EXE-")


def test_execution_ids_continue_within_same_service_instance():
    service = OperationalExecutionService()

    first = service.create_execution(
        action_id="ACTION-1",
        assigned_to="tester",
    )

    second = service.create_execution(
        action_id="ACTION-2",
        assigned_to="tester",
    )

    first_number = int(first.execution_id.removeprefix("EXE-"))
    second_number = int(second.execution_id.removeprefix("EXE-"))

    assert second_number == first_number + 1
