from dairyos.operations.actions.services.operational_action_service import (
    OperationalActionService,
)


def test_create_action():

    service = OperationalActionService()

    action = service.create_action(
        title="Arrange emergency feed",
        description="Secure alternate feed supply",
        assigned_to="Supervisor",
        department="Feed",
    )

    assert action.status.status == "OPEN"
    assert action.assignment.assigned_to == "Supervisor"
