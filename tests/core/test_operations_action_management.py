from dairyos.operations.actions.services.operational_action_service import (
    OperationalActionService,
)

from dairyos.operations.actions.services.action_tracking_service import (
    ActionTrackingService,
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


def test_update_action_status():

    service = OperationalActionService()

    action = service.create_action(
        title="Veterinary review",
        description="Review sick animal",
        assigned_to="Veterinarian",
        department="Health",
    )

    ActionTrackingService().update_status(
        action,
        "COMPLETED",
    )

    assert action.status.status == "COMPLETED"

