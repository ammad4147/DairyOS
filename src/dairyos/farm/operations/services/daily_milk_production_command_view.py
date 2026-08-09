from dataclasses import dataclass, field


@dataclass(frozen=True)
class DailyMilkProductionCommandView:
    """
    Read-only command view for daily milk operations.

    Source:
        Milk production intelligence projections.

    Does not:
        - create production facts
        - modify operational state
        - replace manual entries

    Provides:
        - daily production command summary
        - execution compliance
        - exception awareness
    """


    total_litres: float = 0.0


    production_status: str = "UNKNOWN"


    session_compliance: dict = field(
        default_factory=dict
    )


    production_trend: dict = field(
        default_factory=dict
    )


    yield_variance: dict = field(
        default_factory=dict
    )


    group_yield: dict = field(
        default_factory=dict
    )


    exceptions: list = field(
        default_factory=list
    )


    signals: list = field(
        default_factory=list
    )



    def summary(self):

        return {

            "total_litres":
                self.total_litres,


            "production_status":
                self.production_status,


            "session_compliance":
                self.session_compliance,


            "production_trend":
                self.production_trend,


            "yield_variance":
                self.yield_variance,


            "group_yield":
                self.group_yield,


            "exceptions":
                self.exceptions,


            "signals":
                self.signals,

        }
