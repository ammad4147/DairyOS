from dairyos.intelligence.operations.health.models.farm_health_report import (
    FarmHealthReport,
)



class FarmHealthService:
    """
    Evaluates dairy operational health.

    Converts farm indicators into
    management priorities.

    Does not execute actions.
    """


    def evaluate(
        self,
        situation,
    ):


        factors = []

        actions = []


        if situation.milk_change_percentage < -5:

            factors.append(
                "Milk production decline detected"
            )

            actions.append(
                "Investigate milk production decline"
            )


        if situation.animals_requiring_attention > 0:

            factors.append(
                "Animals require attention"
            )

            actions.append(
                "Review animals requiring attention"
            )


        if situation.reproduction_alerts > 0:

            factors.append(
                "Reproduction alerts detected"
            )

            actions.append(
                "Review reproduction status"
            )


        if len(factors) == 0:

            status = "GOOD"

            risk = "LOW"

            concern = (
                "No significant operational risks detected"
            )


        elif len(factors) == 1:

            status = "MONITOR"

            risk = "MEDIUM"

            concern = factors[0]


        else:

            status = "ATTENTION"

            risk = "HIGH"

            concern = factors[0]


        return FarmHealthReport(

            overall_status=status,

            risk_level=risk,

            primary_concern=concern,

            contributing_factors=factors,

            recommended_actions=actions,
        )
