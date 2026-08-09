from dairyos.operations.commands.handlers.command_handler import (
    CommandHandler,
)


from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)


class MilkProductionHandler(CommandHandler):
    """
    Handles milk production recording commands.
    """


    def __init__(
        self,
        event_publisher,
    ):

        self.event_publisher = event_publisher



    def handle(
        self,
        command,
    ):

        event = OperationalEvent(

            event_type="production",

            entity_type="milk_record",

            entity_id=command.payload.get(
                "animal_id",
                "unknown",
            ),

            actor=command.actor,

            payload=command.payload,

        )


        self.event_publisher.publish(
            event
        )


        return event
