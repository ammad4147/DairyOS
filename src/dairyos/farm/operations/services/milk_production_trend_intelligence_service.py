from dairyos.farm.operations.services.milk_production_trend_intelligence import (
    MilkProductionTrendIntelligence,
)


class MilkProductionTrendIntelligenceService:
    """
    Generates milk production movement intelligence.

    Source:
        MilkProductionIntelligenceService output.

    No operational mutation.
    """


    def __init__(
        self,
        milk_production_intelligence_service,
    ):

        self.milk_production_intelligence_service = (
            milk_production_intelligence_service
        )


    def generate(
        self,
        previous_total_litres: float = 0.0,
    ):

        current = (
            self.milk_production_intelligence_service
            .generate()
        )


        current_total = (
            current.total_litres
        )


        variance = (
            current_total
            -
            previous_total_litres
        )


        percentage = 0.0


        if previous_total_litres > 0:

            percentage = (
                variance
                /
                previous_total_litres
            ) * 100


        direction = "STABLE"


        if variance > 0:

            direction = "INCREASING"


        elif variance < 0:

            direction = "DECREASING"



        signals = []


        if direction == "DECREASING":

            signals.append(
                "Milk production decreased compared with previous reference."
            )


        return MilkProductionTrendIntelligence(

            current_total_litres=current_total,

            previous_total_litres=previous_total_litres,

            variance_litres=variance,

            variance_percentage=percentage,

            trend_direction=direction,

            signals=signals,

        )
