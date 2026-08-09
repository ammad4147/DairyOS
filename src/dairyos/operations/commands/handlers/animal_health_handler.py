from dairyos.operations.commands.handlers.command_handler import (
    CommandHandler,
)


from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)



class AnimalHealthHandler(CommandHandler):
    """
    Handles animal health observations.
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

            event_type="health",

            entity_type="animal",

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
