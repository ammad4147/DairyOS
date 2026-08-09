from dairyos.platform.digital_twin.decision.models.digital_twin_signal import (
    DigitalTwinSignal,
)



class DecisionBridge:
    """
    Converts digital twin insights into
    autonomous intelligence signals.
    """



    def create_signal(

        self,

        metric,

        forecast_change,

        confidence,

    ):


        severity = "low"



        if abs(forecast_change) > 10:

            severity = "medium"



        if abs(forecast_change) > 25:

            severity = "high"



        return DigitalTwinSignal(

            source="digital_twin",

            metric=metric,

            severity=severity,

            message=(

                f"{metric} forecast changed "

                f"by {forecast_change}%"

            ),

            confidence=confidence,

        )

