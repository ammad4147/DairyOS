from dairyos.feed.intelligence.integration import (
    FeedSignalBridge,
    FeedDecisionAdapter,
)

from dairyos.feed.intelligence.models import (
    FeedSignal,
    FeedSignalType,
    FeedSignalSeverity,
)


def create_signal():

    return FeedSignal(
        signal_type=FeedSignalType.INTAKE_VARIANCE,
        severity=FeedSignalSeverity.HIGH,
        animal_group="MILKING_COWS",
        expected_intake=25,
        actual_intake=20,
        variance_percentage=-20,
        message="Feed intake variance -20%",
    )


def test_feed_signal_bridge():

    bridge = FeedSignalBridge()

    intelligence_signal = bridge.convert(
        create_signal()
    )

    assert intelligence_signal.source == "FEED_OS"
    assert intelligence_signal.category == "INTAKE_VARIANCE"
    assert intelligence_signal.severity == "HIGH"
    assert "MILKING_COWS" in intelligence_signal.message


def test_feed_decision_adapter():

    adapter = FeedDecisionAdapter()

    context = adapter.build_context(
        create_signal()
    )

    assert context["domain"] == "FEED"
    assert context["animal_group"] == "MILKING_COWS"
    assert context["requires_attention"] is True
