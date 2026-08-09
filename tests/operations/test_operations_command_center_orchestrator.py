from dairyos.app import container

from dairyos.operations.command_center.operations_command_center_orchestrator import (
    OperationsCommandCenterOrchestrator,
)


def test_command_center_contains_accountability_projection():

    orchestrator = (
        OperationsCommandCenterOrchestrator(
            container.runtime
        )
    )

    view = (
        orchestrator.generate_command_center()
    )

    assert "accountability" in view

    assert (
        "assigned"
        in view["accountability"]
    )

    assert (
        "completed"
        in view["accountability"]
    )
