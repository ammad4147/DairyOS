from dairyos.intelligence.kernel.context.intelligence_context import (
    IntelligenceContext,
)

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)

from dairyos.intelligence.kernel.models.intelligence_decision import (
    IntelligenceDecision,
)


def test_intelligence_context_tracks_operational_state():

    context = IntelligenceContext()

    signal = IntelligenceSignal(
        source="production",
        category="milk",
        message="Production below target",
    )

    decision = IntelligenceDecision(
        action="Review feed",
        rationale="Production signal",
    )

    context.add_signal(signal)
    context.add_decision(decision)

    summary = context.summary()

    assert summary["signals"] == 1
    assert summary["decisions"] == 1
    assert summary["outcomes"] == 0
