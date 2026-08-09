from datetime import datetime

from ..models.correlated_health_signal import (
    CorrelatedHealthSignal
)



class HealthCorrelationService:



    def evaluate(

        self,

        animal_id,

        signals,

        history=None

    ):

        history = history or []


        risk = "NORMAL"

        reasons = []

        checks = []



        signal_types = [

            signal.signal_type

            for signal in signals

        ]



        if "MILK_YIELD_DROP" in signal_types:

            reasons.append(

                "Milk production decline detected"

            )

            checks.append(

                "Review milk production trend"

            )



        if "FEED_INTAKE_DROP" in signal_types:

            reasons.append(

                "Reduced feed intake detected"

            )

            checks.append(

                "Review feed intake and ration"

            )



        if len(signals) >= 2:

            risk = "MEDIUM"



        if len(history) > 0:

            reasons.append(

                "Previous health history available"

            )

            risk = "HIGH"



        return CorrelatedHealthSignal(

            animal_id,

            signals,

            risk,

            reasons,

            checks,

            datetime.now()

        )
