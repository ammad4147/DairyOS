from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)

from dairyos.intelligence.kernel.models.intelligence_decision import (
    IntelligenceDecision,
)

from dairyos.intelligence.kernel.models.intelligence_outcome import (
    IntelligenceOutcome,
)

from dairyos.intelligence.kernel.registry.signal_registry import (
    SignalRegistry,
)

from dairyos.intelligence.kernel.services.signal_evaluator import (
    SignalEvaluator,
)

from dairyos.intelligence.kernel.services.intelligence_bridge import (
    IntelligenceBridge,
)


def test_intelligence_kernel_signal_to_decision_flow():

    signal = IntelligenceSignal(
        source="herd",
        category="health",
        message="Animal health risk detected",
        severity="critical",
    )

    registry = SignalRegistry()

    registry.register(signal)

    evaluator = SignalEvaluator(registry)

    outcomes = evaluator.evaluate_outcomes()

    assert len(outcomes) == 1

    assert isinstance(
        outcomes[0],
        IntelligenceOutcome,
    )

    assert outcomes[0].status == "generated"


def test_intelligence_bridge_generates_decision():

    signal = IntelligenceSignal(
        source="operations",
        category="delay",
        message="Feed delivery delayed",
        severity="critical",
    )

    bridge = IntelligenceBridge()

    decision = bridge.evaluate_signal(signal)

    assert isinstance(
        decision,
        IntelligenceDecision,
    )

    assert decision.priority == "high"

    assert decision.action == "Immediate attention required"
