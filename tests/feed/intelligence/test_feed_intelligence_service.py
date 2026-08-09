from dairyos.feed.intelligence import FeedIntelligenceService
from dairyos.feed.intelligence.models import FeedSignalSeverity


def test_high_feed_variance_detection():

    service = FeedIntelligenceService()


    signal = service.detect_intake_variance(
        animal_group="MILKING_COWS",
        expected_intake=25,
        actual_intake=20,
    )


    assert signal.severity == FeedSignalSeverity.HIGH



def test_medium_feed_variance_detection():

    service = FeedIntelligenceService()


    signal = service.detect_intake_variance(
        animal_group="MILKING_COWS",
        expected_intake=25,
        actual_intake=23,
    )


    assert signal.severity == FeedSignalSeverity.MEDIUM



def test_low_feed_variance_detection():

    service = FeedIntelligenceService()


    signal = service.detect_intake_variance(
        animal_group="MILKING_COWS",
        expected_intake=25,
        actual_intake=24,
    )


    assert signal.severity == FeedSignalSeverity.LOW
