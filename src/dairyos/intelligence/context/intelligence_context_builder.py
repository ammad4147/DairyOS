class IntelligenceContextBuilder:
    """
    Converts operational state into intelligence input context.

    Rules:
    - Reads operational facts only.
    - Does not mutate FarmOperationalState.
    - Does not create operational records.
    - Produces intelligence-ready observations.
    """



    def build(
        self,
        state,
    ):

        return {

            "farm_id":
                state.farm_id,


            "operational_date":
                state.operational_date,


            "milk_status":
                dict(
                    state.milk_status
                ),


            "milk_total":
                state.milk_total(),


            "feeding_status":
                dict(
                    state.feeding_status
                ),


            "feed_total":
                state.feed_total(),


            "health_alerts":
                list(
                    state.health_alerts
                ),


            "health_alert_count":
                state.health_alert_count(),


            "breeding_status":
                dict(
                    state.breeding_status
                ),


            "workforce_status":
                dict(
                    state.workforce_status
                ),


            "inventory_status":
                dict(
                    state.inventory_status
                ),


            "equipment_status":
                dict(
                    state.equipment_status
                ),


            "open_tasks":
                list(
                    state.open_tasks
                ),

        }
