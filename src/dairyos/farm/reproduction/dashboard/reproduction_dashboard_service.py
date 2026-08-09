class ReproductionDashboardService:
    """
    Creates reproduction indicators.
    """



    def __init__(
        self,
        service,
    ):

        self.service = service



    def daily_summary(
        self,
    ):


        pregnant = (
            self.service.pregnant_animals()
        )


        return {

            "pregnant_animals":
                len(pregnant),


            "reproduction_status":
                (
                    "normal"
                    if pregnant
                    else
                    "attention"
                ),

        }
