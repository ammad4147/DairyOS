from dairyos.intelligence.operations.dashboard.models.farm_command_view import (
    FarmCommandView,
)


class FarmCommandBuilder:
    """
    Builds owner dashboard information.
    """


    def build(
        self,
        situation,
    ):

        return FarmCommandView(

            total_animals=situation.total_animals,

            milking_cows=situation.milking_cows,

            dry_cows=situation.dry_cows,

            close_up_cows=situation.close_up_cows,


            daily_milk_litres=situation.daily_milk_litres,

            previous_day_milk_litres=0,


            milk_change_percentage=(
                situation.milk_change_percentage
            ),


            feed_cost_per_litre=(
                situation.feed_cost_per_litre
            ),


            animals_requiring_attention=(
                situation.animals_requiring_attention
            ),


            reproduction_alerts=(
                situation.reproduction_alerts
            ),


            active_tasks=0,


            overall_status=(
                situation.overall_status
            ),
        )
