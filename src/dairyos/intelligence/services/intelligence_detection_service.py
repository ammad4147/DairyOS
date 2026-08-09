from dairyos.intelligence.models.intelligence_signal import (
    IntelligenceSignal,
)


class IntelligenceDetectionService:
    """
    Converts operational measurements into intelligence signals.

    Detection only.
    No operational state mutation.
    """


    def detect_milk_variance(
        self,
        actual_litres,
        expected_litres,
    ):

        variance = (
            actual_litres
            -
            expected_litres
        )


        if variance >= 0:

            return None


        severity = "WARNING"


        if abs(variance) > expected_litres * 0.25:

            severity = "CRITICAL"


        return IntelligenceSignal(

            signal_type="MILK_PRODUCTION_VARIANCE",

            severity=severity,

            source="milk_production",

            evidence={

                "actual_litres":
                    actual_litres,

                "expected_litres":
                    expected_litres,

                "variance":
                    variance,

            },

            message=
                "Milk production is below expected level",

        )

