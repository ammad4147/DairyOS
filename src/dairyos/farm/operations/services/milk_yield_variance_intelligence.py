from dataclasses import dataclass, field


@dataclass(frozen=True)
class MilkYieldVarianceIntelligence:
    """
    Read-only intelligence projection for
    milk production variance.

    Source:
        Verified milk production facts
        compared against explicit targets.

    Does not:
        - create production targets
        - modify milk records
        - estimate missing production

    Provides:
        - variance analysis
        - exception signals
    """


    actual_production: float = 0.0


    expected_production: float = 0.0


    variance: float = 0.0


    variance_percentage: float = 0.0


    variance_status: str = "UNKNOWN"


    exceptions: list = field(
        default_factory=list
    )



    def summary(self):

        return {

            "actual_production":
                self.actual_production,


            "expected_production":
                self.expected_production,


            "variance":
                self.variance,


            "variance_percentage":
                self.variance_percentage,


            "variance_status":
                self.variance_status,


            "exceptions":
                self.exceptions,

        }
