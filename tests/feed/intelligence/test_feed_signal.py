from dairyos.feed.intelligence.models import (
    FeedSignal,
    FeedSignalType,
    FeedSignalSeverity,
)


def test_feed_signal_creation():

    signal = FeedSignal(
        signal_type=FeedSignalType.INTAKE_VARIANCE,
        severity=FeedSignalSeverity.HIGH,
        animal_group="MILKING_COWS",
        expected_intake=25,
        actual_intake=20,
        variance_percentage=-20,
        message="Low intake detected",
    )


    assert signal.animal_group == "MILKING_COWS"
    assert signal.severity == FeedSignalSeverity.HIGH
    assert signal.variance_percentage == -20
