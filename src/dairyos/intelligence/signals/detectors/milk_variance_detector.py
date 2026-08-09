from dairyos.intelligence.signals.signal_detector import (
    SignalDetector,
)

from dairyos.intelligence.models.intelligence_signal import (
    IntelligenceSignal,
)



class MilkVarianceDetector(
    SignalDetector
):
    """
    Detects milk production below expectation.

    Detection only.
    Does not modify operational state.
    """



    def detect(
        self,
        operational_context,
    ):

        if (
            "actual_litres"
            not in operational_context
            or
            "expected_litres"
            not in operational_context
        ):

            return None


        actual_litres = (
            operational_context[
                "actual_litres"
            ]
        )


        expected_litres = (
            operational_context[
                "expected_litres"
            ]
        )


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

            signal_type=
                "MILK_PRODUCTION_VARIANCE",

            severity=
                severity,

            source=
                "milk_production",

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
