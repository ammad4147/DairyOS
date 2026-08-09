from dairyos.intelligence.execution.gateway.execution_gateway import (
    ExecutionGateway,
)


class FakeCoordinator:

    def __init__(self):
        self.received = None


    def execute(
        self,
        **kwargs,
    ):

        self.received = kwargs

        return {
            "status": "executed",
            "payload": kwargs,
        }


def test_execution_gateway_enterprise_execution_contract():

    coordinator = FakeCoordinator()

    gateway = ExecutionGateway(
        coordinator
    )


    result = gateway.execute(
        workflow_type="operational",
        objective="test autonomous workflow",
        priority="high",
        task_name="runtime validation",
        assigned_to="farm_operator",
        queue_name="operations",
    )


    assert result["status"] == "executed"

    assert (
        coordinator.received["workflow_type"]
        == "operational"
    )

    assert (
        coordinator.received["priority"]
        == "high"
    )


def test_execution_gateway_legacy_execution_contract():

    coordinator = FakeCoordinator()

    gateway = ExecutionGateway(
        coordinator
    )


    result = gateway.execute(
        task="legacy task"
    )


    assert result["status"] == "executed"

    assert (
        coordinator.received["task"]
        == "legacy task"
    )


def test_execution_gateway_get_coordinator():

    coordinator = FakeCoordinator()

    gateway = ExecutionGateway(
        coordinator
    )


    assert (
        gateway.get_coordinator()
        is coordinator
    )
