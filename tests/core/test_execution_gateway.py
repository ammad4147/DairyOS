from dairyos.intelligence.execution.gateway.execution_gateway import (
    ExecutionGateway,
)

from dairyos.intelligence.execution.services.execution_coordinator import (
    ExecutionCoordinator,
)


def test_gateway_returns_coordinator():

    coordinator = ExecutionCoordinator()

    gateway = ExecutionGateway(
        coordinator,
    )

    assert gateway.get_coordinator() is coordinator
