from dairyos.intelligence.kernel.memory.intelligence_memory import (
    IntelligenceMemory,
)

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)

from dairyos.intelligence.kernel.models.intelligence_decision import (
    IntelligenceDecision,
)


def test_intelligence_memory_stores_signal_and_decision():

    memory = IntelligenceMemory()

    signal = IntelligenceSignal(
        source="health",
        category="animal_health",
        message="Temperature abnormal",
    )

    decision = IntelligenceDecision(
        action="Inspect animal",
        rationale="Health signal received",
    )

    memory.store_signal(signal)
    memory.store_decision(decision)

    assert memory.signal_count() == 1
    assert memory.decision_count() == 1

    assert memory.get_signals()[0].source == "health"
    assert memory.get_decisions()[0].action == "Inspect animal"
