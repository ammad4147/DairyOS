from datetime import datetime

from ..models.correlated_health_signal import CorrelatedHealthSignal
from ..models.health_alert import HealthAlert
from dairyos.core.time_utils import utcnow


class HealthRiskAssessmentService:


    def assess(
        self,
        animal_id,
        signals,
        observations=None,
        examiner="DairyOS"
    ):

        observations = observations or []

        reasons = []

        recommended_checks = []

        risk_level = "NORMAL"


        for signal in signals:

            if signal.severity.upper() == "HIGH":

                risk_level = "HIGH"

            elif (
                signal.severity.upper() == "MEDIUM"
                and risk_level != "HIGH"
            ):

                risk_level = "MEDIUM"


            reasons.append(

                f"{signal.signal_type} detected"

            )


        for observation in observations:

            if observation.severity.upper() == "HIGH":

                risk_level = "HIGH"


            elif (
                observation.severity.upper() == "MEDIUM"
                and risk_level != "HIGH"
            ):

                risk_level = "MEDIUM"


            reasons.append(

                observation.observation_type

                +

                " observation recorded"

            )


        if "MILK_YIELD_DROP" in [
            signal.signal_type
            for signal in signals
        ]:

            recommended_checks.extend(

                [
                    "Check feed intake",
                    "Perform clinical examination",
                    "Review milk quality"
                ]

            )


        if any(

            "UDDER"

            in reason.upper()

            for reason in reasons

        ):

            recommended_checks.append(

                "Mastitis screening"

            )


        if risk_level == "HIGH":

            recommended_checks.append(

                "Veterinary examination"

            )


        correlated = CorrelatedHealthSignal(

            animal_id,

            signals,

            risk_level,

            reasons,

            recommended_checks,

            utcnow()

        )


        return correlated



    def create_alert(

        self,

        assessment,

        assigned_to="Veterinarian"

    ):


        if assessment.risk_level == "NORMAL":

            status = "MONITOR"

        else:

            status = "OPEN"


        return HealthAlert(

            assessment.animal_id,

            "HEALTH_RISK",

            assessment.risk_level,

            "; ".join(

                assessment.reasons

            ),

            assigned_to,

            status,

            utcnow()

        )
