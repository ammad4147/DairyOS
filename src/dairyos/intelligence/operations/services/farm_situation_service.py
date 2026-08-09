from dairyos.intelligence.operations.models.farm_situation import (
    FarmSituation,
)



class FarmSituationService:
    """
    Evaluates current dairy farm conditions.

    Converts operational measurements into
    a management situation snapshot.

    Responsibility boundary:

    Farm reality -> Situation understanding
    """


    def evaluate(
        self,
        total_animals: int,
        milking_cows: int,
        dry_cows: int,
        close_up_cows: int,
        animals_requiring_attention: int,
        daily_milk_litres: float,
        previous_day_milk_litres: float,
        feed_cost_per_litre: float,
        reproduction_alerts: int,
    ):

        milk_change_percentage = 0


        if previous_day_milk_litres > 0:

            milk_change_percentage = (
                (
                    (
                        daily_milk_litres
                        -
                        previous_day_milk_litres
                    )
                    /
                    previous_day_milk_litres
                )
                * 100
            )


        if (
            animals_requiring_attention > 0
            or
            milk_change_percentage < -5
            or
            reproduction_alerts > 0
        ):

            overall_status = "ATTENTION"


        elif milk_change_percentage < 0:

            overall_status = "MONITOR"


        else:

            overall_status = "GOOD"



        return FarmSituation(

            total_animals=total_animals,

            milking_cows=milking_cows,

            dry_cows=dry_cows,

            close_up_cows=close_up_cows,

            animals_requiring_attention=animals_requiring_attention,

            daily_milk_litres=daily_milk_litres,

            milk_change_percentage=round(
                milk_change_percentage,
                2,
            ),

            feed_cost_per_litre=feed_cost_per_litre,

            reproduction_alerts=reproduction_alerts,

            overall_status=overall_status,
        )
