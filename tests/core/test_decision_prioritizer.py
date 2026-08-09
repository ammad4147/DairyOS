from dairyos.intelligence.kernel.context.intelligence_context import (
    IntelligenceContext,
)

from dairyos.intelligence.kernel.prioritization.decision_prioritizer import (
    DecisionPrioritizer,
)

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)


def test_decision_prioritizer_ranks_critical_signal_first():

    context = IntelligenceContext()

    context.add_signal(
        IntelligenceSignal(
            source="health",
            category="animal_health",
            message="Critical temperature alert",
            severity="critical",
        )
    )

    context.add_signal(
        IntelligenceSignal(
            source="production",
            category="milk",
            message="Production variance",
            severity="normal",
        )
    )


    prioritizer = DecisionPrioritizer()

    priorities = prioritizer.prioritize(context)


    assert len(priorities) == 2
    assert priorities[0]["priority"] == "immediate"
    assert priorities[0]["source"] == "health"
