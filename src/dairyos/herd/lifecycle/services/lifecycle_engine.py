from ..models.lifecycle_event import LifecycleEvent


class LifecycleEngine:
    """
    Controls animal lifecycle transitions.

    Compatibility preserved:
    - keeps in-memory history for existing consumers/tests
    - optionally publishes lifecycle events downstream

    Publishing is optional because event infrastructure
    is injected from outside.
    """


    def __init__(
        self,
        event_publisher=None,
    ):

        self.history = []

        self.event_publisher = (
            event_publisher
        )


    def transition(
        self,
        animal,
        new_status,
    ):

        event = LifecycleEvent(

            animal_id=animal.animal_id,

            previous_status=(
                animal.status.value
            ),

            new_status=(
                new_status.value
            ),

            location=animal.location,

            event_type="STATUS_CHANGE",

        )


        animal.status = new_status


        self.history.append(
            event
        )


        if self.event_publisher:

            self.event_publisher.publish(
                event
            )


        return event
