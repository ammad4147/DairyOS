from dairyos.intelligence.kernel.models.intelligence_signal import IntelligenceSignal
from dairyos.intelligence.kernel.registry.signal_registry import IntelligenceSignalRegistry



def test_signal_registry_registers_signal():

    registry = IntelligenceSignalRegistry()

    signal = IntelligenceSignal(
        source="herd",
        category="health",
        message="Temperature anomaly detected",
    )

    registry.register(signal)

    assert registry.count() == 1



def test_signal_registry_returns_registered_signals():

    registry = IntelligenceSignalRegistry()

    signal = IntelligenceSignal(
        source="operations",
        category="workflow",
        message="Feed entry missing",
    )

    registry.register(signal)

    signals = registry.get_all()

    assert signals[0].source == "operations"

