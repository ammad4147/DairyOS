from dairyos.operations.executive.services.executive_operations_service import (
    ExecutiveOperationsService,
)


def test_executive_operations_green():

    service = ExecutiveOperationsService()

    summary = service.generate_summary()

    assert summary.health_status == "GREEN"
    assert summary.owner_action_required is False


def test_executive_operations_priority():

    service = ExecutiveOperationsService()

    summary = service.generate_summary()

    assert summary.operational_priority_score >= 0
