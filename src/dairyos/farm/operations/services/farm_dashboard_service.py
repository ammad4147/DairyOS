from dairyos.farm.operations.services.farm_operations_service import (
    FarmOperationsService,
)


class FarmDashboardService:
    """
    Builds Farm Command Center data.

    Converts operational records
    into management information.
    """


    def __init__(
        self,
        operations_service=None,
    ):

        self.operations_service = (
            operations_service
            if operations_service
            else FarmOperationsService()
        )


    def build_dashboard(
        self,
    ):

        return {

            "milk_today": (
                self.operations_service
                .daily_milk_total()
            ),

            "feed_quantity_today": (
                self.operations_service
                .daily_feed_quantity()
            ),

            "feed_cost_today": (
                self.operations_service
                .daily_feed_cost()
            ),

            "health_alerts": (
                self.operations_service
                .health_attention_count()
            ),

            "breeding_pending": (
                self.operations_service
                .breeding_pending_count()
            ),

            "attention_items": (
                self.operations_service
                .attention_items()
            ),
        }
