from dairyos.operations.health.services.operations_health_service import (
    OperationsHealthService,
)


def test_operations_health_green():

    service = OperationsHealthService()

    snapshot = service.generate_snapshot()

    assert snapshot.health_status == "GREEN"
    assert snapshot.owner_attention_required is False



def test_operations_health_requires_attention():

    service = OperationsHealthService()

    snapshot = service.generate_snapshot(
        pending_actions=8,
    )

    assert snapshot.health_status == "AMBER"
    assert snapshot.owner_attention_required is True
