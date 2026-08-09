from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)


class MilkProductionService:
    """
    Handles milk production domain actions.
    """


    def __init__(
        self,
        event_publisher,
    ):

        self.event_publisher = event_publisher



    def record(
        self,
        command,
    ):


        event = OperationalEvent(

            event_type="production",

            entity_type="cow",

            entity_id=
                command.payload["cow_id"],

            actor=command.actor,

            payload={

                "litres":
                    command.payload["litres"],

                "activity":
                    "milking",

            },

        )


        self.event_publisher.publish(
            event
        )


        return event
