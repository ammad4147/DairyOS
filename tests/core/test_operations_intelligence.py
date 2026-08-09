from datetime import datetime

from dairyos.operations.intelligence.models.operational_signal import (
    OperationalSignal,
)

from dairyos.operations.intelligence.services.operations_intelligence_service import (
    OperationsIntelligenceService,
)


def test_operational_signal_registration():

    service = OperationsIntelligenceService()

    signal = OperationalSignal(
        signal_id="SIG-001",
        category="Feeding",
        description="Morning feeding delayed",
        severity="HIGH",
        source="Farm Operations",
        created_at=datetime.now(),
    )

    service.register_signal(signal)

    assert len(service.active_signals()) == 1


def test_operational_score():

    service = OperationsIntelligenceService()

    score = service.calculate_score(
        total_tasks=100,
        completed_tasks=90,
        delayed_tasks=2,
        critical_issues=1,
    )

    assert score.completion_rate == 90
    assert score.operational_health_score > 70
