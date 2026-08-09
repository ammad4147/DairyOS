class HealthDashboardService:
    """
    Creates health management summary.
    """



    def __init__(
        self,
        service,
    ):

        self.service = service



    def daily_summary(
        self,
    ):

        attention = (
            self.service.animals_needing_attention()
        )


        return {

            "animals_requiring_attention":
                len(attention),


            "health_status":
                (
                    "attention"
                    if attention
                    else
                    "normal"
                ),

        }
