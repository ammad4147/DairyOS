from dairyos.operations.commands.handlers.command_handler import (
    CommandHandler,
)


from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)



class OperationalTaskCommandHandler(
    CommandHandler,
):
    """
    Handles farm operational task commands.
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

            event_type="operations",

            entity_type="task",

            entity_id=command.command_id,

            actor=command.actor,

            payload=command.payload,

        )


        self.event_publisher.publish(
            event
        )


        return event
