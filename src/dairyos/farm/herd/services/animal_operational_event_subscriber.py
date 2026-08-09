from dairyos.farm.herd.services.animal_event_projection import (
    AnimalEventProjection,
)


class AnimalOperationalEventSubscriber:
    """
    Event-bus adapter for animal operational state.

    Ownership:

        FarmOperationEventBus
                |
                v
        AnimalOperationalEventSubscriber
                |
                v
        AnimalEventProjection
    """

    def __init__(self, projection=None):
        self.projection = (
            projection
            if projection is not None
            else AnimalEventProjection()
        )

    def handle(self, event):
        """
        Project one operational event into animal state.
        """

        return self.projection.apply(event)
