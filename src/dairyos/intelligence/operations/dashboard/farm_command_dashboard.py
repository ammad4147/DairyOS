class FarmCommandDashboard:
    """
    Executive operational dashboard.

    Converts farm intelligence
    into daily management view.
    """



    def __init__(
        self,
        situation_service=None,
        health_dashboard=None,
        reproduction_dashboard=None,
    ):

        self.situation_service = (
            situation_service
        )

        self.health_dashboard = (
            health_dashboard
        )

        self.reproduction_dashboard = (
            reproduction_dashboard
        )



    def generate(
        self,
        farm_situation,
        health_summary,
        reproduction_summary,
    ):

        status = (
            "normal"
            if
            health_summary[
                "animals_requiring_attention"
            ] == 0

            else

            "attention"
        )


        return {


            "farm_status":
                status,


            "herd":

                {

                    "total_animals":
                        farm_situation.total_animals,


                    "milking_cows":
                        farm_situation.milking_cows,


                    "dry_cows":
                        farm_situation.dry_cows,


                    "close_up_cows":
                        farm_situation.close_up_cows,

                },


            "production":

                {

                    "daily_milk_litres":
                        farm_situation.daily_milk_litres,


                    "milk_change_percentage":
                        farm_situation.milk_change_percentage,


                    "feed_cost_per_litre":
                        farm_situation.feed_cost_per_litre,

                },


            "health":
                health_summary,


            "reproduction":
                reproduction_summary,


            "actions":

                [

                    "Review health alerts",

                    "Review reproduction schedule",

                    "Monitor production trend",

                ],

        }
