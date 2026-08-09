from dairyos.farm.command_center.models.attention_item import (
    AttentionItem,
)


class AttentionQueueService:
    """
    Builds the owner attention queue.

    This service only aggregates
    existing operational signals.

    It does not create business events.
    """

    def __init__(
        self,
        *,
        missing_input_detection_service=None,
    ):

        self.missing_input_detection_service = (
            missing_input_detection_service
        )


    def build(
        self,
        *,
        farm_state,
    ):

        items = []


        health_alerts = getattr(
            farm_state,
            "health_alerts",
            [],
        )


        for alert in health_alerts:

            items.append(

                AttentionItem(

                    priority=alert.get(
                        "severity",
                        "UNKNOWN",
                    ),

                    area="HEALTH",

                    message=alert.get(
                        "observation",
                        "Health issue detected",
                    ),

                    animal_id=alert.get(
                        "animal_id",
                    ),

                )

            )


        if self.missing_input_detection_service:

            gaps = (
                self.missing_input_detection_service.detect(
                    farm_state
                )
            )


            for gap in gaps:

                items.append(

                    AttentionItem(

                        priority=gap.severity,

                        area=gap.area,

                        message=gap.message,

                    )

                )


        return items
