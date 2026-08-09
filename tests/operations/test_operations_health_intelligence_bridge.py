from dairyos.operations.health.services.operations_health_intelligence_bridge import (
    OperationsHealthIntelligenceBridge,
)


def test_operations_health_intelligence_bridge():

    bridge = (
        OperationsHealthIntelligenceBridge()
    )


    snapshot = (
        bridge.generate_snapshot(
            total_tasks=10,
            completed_tasks=9,
            delayed_tasks=1,
            critical_issues=0,
        )
    )


    assert snapshot.health_status == "GREEN"

    assert snapshot.operational_score == 88.0

    assert snapshot.owner_attention_required is False
