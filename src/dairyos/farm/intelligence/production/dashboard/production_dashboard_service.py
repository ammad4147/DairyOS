class ProductionDashboardService:
    """
    Converts production efficiency
    into management dashboard data.
    """



    def create(
        self,
        efficiency,
    ):


        return {

            "milk_today":
                efficiency.milk_litres,


            "milk_per_cow":
                efficiency.litres_per_animal,


            "feed_cost_per_litre":
                efficiency.feed_cost_per_litre,


            "status":
                efficiency.efficiency_status,

        }
