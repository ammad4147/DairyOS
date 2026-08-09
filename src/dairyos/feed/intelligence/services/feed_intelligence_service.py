from dairyos.feed.intelligence.models import (
    FeedSignal,
    FeedSignalType,
    FeedSignalSeverity,
)


class FeedIntelligenceService:


    def detect_intake_variance(
        self,
        animal_group: str,
        expected_intake: float,
        actual_intake: float,
    ) -> FeedSignal:


        if expected_intake == 0:
            variance = 0

        else:
            variance = (
                (actual_intake - expected_intake)
                /
                expected_intake
            ) * 100


        severity = FeedSignalSeverity.LOW


        # Dairy operational early-warning thresholds
        #
        # Small intake drops are treated seriously because
        # reduced intake can precede:
        # - milk decline
        # - rumen problems
        # - health events
        #
        if abs(variance) >= 20:
            severity = FeedSignalSeverity.HIGH

        elif abs(variance) >= 5:
            severity = FeedSignalSeverity.MEDIUM


        return FeedSignal(
            signal_type=FeedSignalType.INTAKE_VARIANCE,
            severity=severity,
            animal_group=animal_group,
            expected_intake=expected_intake,
            actual_intake=actual_intake,
            variance_percentage=variance,
            message=f"Feed intake variance {variance:.2f}%"
        )
