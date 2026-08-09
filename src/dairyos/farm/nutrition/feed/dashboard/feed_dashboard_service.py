class FeedDashboardService:
    """
    Creates feed management indicators.
    """



    def __init__(
        self,
        service,
    ):

        self.service = service



    def daily_summary(
        self,
    ):

        quantity = (
            self.service.total_feed_kg()
        )

        cost = (
            self.service.total_feed_cost()
        )


        return {

            "feed_quantity_kg":
                quantity,

            "feed_cost":
                cost,

            "status":
                "normal"
                if quantity > 0
                else "attention",
        }
