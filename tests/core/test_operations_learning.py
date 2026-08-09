from dairyos.operations.learning.models.learning_signal import LearningSignal
from dairyos.operations.learning.services.learning_service import LearningService
from dairyos.operations.learning.services.pattern_detection_service import (
    PatternDetectionService,
)
from dairyos.operations.learning.services.improvement_service import (
    ImprovementService,
)


def test_learning_signal_recording():

    service = LearningService()

    signal = LearningSignal(
        signal_id="SIG-001",
        category="Feeding",
        description="Feed delivery delayed",
        impact_level="HIGH",
        created_at=None,
    )

    service.record_signal(signal)

    assert len(service.get_signals()) == 1


def test_pattern_detection():

    service = LearningService()

    service.record_signal(
        LearningSignal(
            signal_id="SIG-001",
            category="Feeding",
            description="Delay",
            impact_level="HIGH",
            created_at=None,
        )
    )

    service.record_signal(
        LearningSignal(
            signal_id="SIG-002",
            category="Feeding",
            description="Delay again",
            impact_level="HIGH",
            created_at=None,
        )
    )

    patterns = PatternDetectionService().detect_patterns(
        service.get_signals()
    )

    assert len(patterns) == 1


def test_improvement_creation():

    opportunities = ImprovementService().create_opportunities(
        []
    )

    assert opportunities == []
