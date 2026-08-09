from dataclasses import dataclass, field


@dataclass(frozen=True)
class MilkProductionTrendIntelligence:
    """
    Read-only milk production trend analytics.

    Source:
        Verified milk production intelligence.

    Does not:
        - create milk records
        - modify operational state
        - infer missing production data

    Provides:
        - production comparison
        - trend direction
        - operational signals
    """


    current_total_litres: float = 0.0


    previous_total_litres: float = 0.0


    variance_litres: float = 0.0


    variance_percentage: float = 0.0


    trend_direction: str = "UNKNOWN"


    signals: list = field(
        default_factory=list
    )


    def summary(self):

        return {

            "current_total_litres":
                self.current_total_litres,

            "previous_total_litres":
                self.previous_total_litres,

            "variance_litres":
                self.variance_litres,

            "variance_percentage":
                self.variance_percentage,

            "trend_direction":
                self.trend_direction,

            "signals":
                self.signals,

        }
