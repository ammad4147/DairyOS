from dataclasses import dataclass, field



@dataclass
class IntelligenceSummary:
    """
    Dashboard-safe intelligence projection.

    Represents intelligence observations only.

    Does not:
    - modify operational state
    - execute recommendations
    - create farm events
    """

    signal_count: int = 0

    critical_signal_count: int = 0

    warning_signal_count: int = 0

    signals: list = field(
        default_factory=list
    )

    recommendations: list = field(
        default_factory=list
    )



    @classmethod
    def from_pipeline_result(
        cls,
        result,
    ):

        signals = (
            result.get(
                "signals",
                []
            )
        )


        recommendations = (
            result.get(
                "recommendations",
                []
            )
        )


        critical_count = 0

        warning_count = 0


        for signal in signals:

            severity = getattr(
                signal,
                "severity",
                None,
            )


            if severity == "CRITICAL":

                critical_count += 1


            elif severity == "WARNING":

                warning_count += 1



        return cls(

            signal_count=len(
                signals
            ),

            critical_signal_count=critical_count,

            warning_signal_count=warning_count,

            signals=signals,

            recommendations=recommendations,

        )

