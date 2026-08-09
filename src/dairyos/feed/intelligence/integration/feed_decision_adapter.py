from dairyos.feed.intelligence.models import FeedSignal


class FeedDecisionAdapter:
    """
    Creates intelligence decision context
    from FeedOS signals.
    """

    def build_context(
        self,
        feed_signal: FeedSignal,
    ) -> dict:

        requires_attention = feed_signal.severity.value in (
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        )

        return {
            "domain": "FEED",
            "animal_group": feed_signal.animal_group,
            "signal_type": feed_signal.signal_type.value,
            "severity": feed_signal.severity.value,
            "message": feed_signal.message,
            "expected_intake": feed_signal.expected_intake,
            "actual_intake": feed_signal.actual_intake,
            "variance_percentage": feed_signal.variance_percentage,
            "requires_attention": requires_attention,
        }
