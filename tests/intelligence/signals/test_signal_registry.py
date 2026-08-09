from dairyos.intelligence.signals.signal_registry import (
    SignalRegistry,
)


from dairyos.intelligence.models.intelligence_signal import (
    IntelligenceSignal,
)



class TestDetector:

    def detect(
        self,
        operational_context,
    ):

        return IntelligenceSignal(

            signal_type="TEST_SIGNAL",

            severity="INFO",

            source="test",

            message="Test signal",

        )



def test_signal_registry_registers_detector():

    registry = SignalRegistry()


    registry.register(
        TestDetector()
    )


    signals = registry.evaluate(
        {}
    )


    assert len(signals) == 1

    assert (
        signals[0].signal_type
        ==
        "TEST_SIGNAL"
    )



def test_signal_registry_starts_empty():

    registry = SignalRegistry()


    signals = registry.evaluate(
        {}
    )


    assert signals == []
