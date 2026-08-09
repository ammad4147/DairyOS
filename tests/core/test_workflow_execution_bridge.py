from dairyos.intelligence.execution.integration.workflow_execution_bridge import (
    WorkflowExecutionBridge,
)

from dairyos.intelligence.execution.services.execution_coordinator import (
    ExecutionCoordinator,
)


def test_bridge_returns_execution_coordinator():

    bridge = WorkflowExecutionBridge()

    coordinator = bridge.coordinator_instance()

    assert isinstance(
        coordinator,
        ExecutionCoordinator,
    )
