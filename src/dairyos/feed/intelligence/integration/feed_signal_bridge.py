from dairyos.feed.intelligence.models import FeedSignal
from dairyos.intelligence.kernel.models import IntelligenceSignal


class FeedSignalBridge:
    """
    Converts FeedOS signals into DairyOS intelligence signals.
    """

    def convert(
        self,
        feed_signal: FeedSignal,
    ) -> IntelligenceSignal:

        message = (
            f"Feed intake variance detected for "
            f"{feed_signal.animal_group}: "
            f"{feed_signal.variance_percentage:.2f}%"
        )

        return IntelligenceSignal(
            source="FEED_OS",
            category=feed_signal.signal_type.value,
            message=message,
            severity=feed_signal.severity.value,
        )
