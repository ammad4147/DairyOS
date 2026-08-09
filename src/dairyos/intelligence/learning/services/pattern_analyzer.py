from dairyos.intelligence.learning.models.learning_signal import (
    LearningSignal,
)


class PatternAnalyzer:
    """
    Deterministic intelligence pattern analyzer.

    Converts historical intelligence events
    into reusable learning signals.

    Future extensions:

    - statistical analysis
    - machine learning models
    - predictive learning
    """


    def analyze(
        self,
        events: list,
    ) -> list[LearningSignal]:

        signals = []


        critical_events = 0


        for event in events:

            if (
                event.event_type
                == "signal_received"
                and event.payload.get(
                    "severity"
                )
                == "critical"
            ):

                critical_events += 1


        if critical_events > 0:

            signals.append(
                LearningSignal(
                    category=(
                        "operational_risk"
                    ),
                    description=(
                        "Critical intelligence "
                        "events detected in history"
                    ),
                    confidence=(
                        min(
                            critical_events / 10,
                            1.0,
                        )
                    ),
                )
            )


        return signals
