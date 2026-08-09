from dairyos.operations.milk.commands.services.milk_production_handler import (
    MilkProductionCommandHandler,
)

from dairyos.operations.milk.services.milk_production_service import (
    MilkProductionService,
)

from dairyos.operations.commands.handlers.animal_health_handler import (
    AnimalHealthHandler,
)

from dairyos.operations.commands.handlers.animal_operational_review_handler import (
    AnimalOperationalReviewHandler,
)



class OperationalCommandRegistry:
    """
    Registers operational command handlers.

    Central command boundary.
    """


    def __init__(
        self,
        dispatcher,
        event_publisher,
    ):

        self.dispatcher = dispatcher

        self.event_publisher = event_publisher



    def register_defaults(
        self,
    ):


        #
        # Milk commands
        #

        milk_service = MilkProductionService(
            self.event_publisher
        )


        milk_handler = MilkProductionCommandHandler(
            milk_service
        )


        self.dispatcher.register(

            "milk_production_recorded",

            milk_handler.handle,

        )



        #
        # Animal health commands
        #

        animal_health_handler = AnimalHealthHandler(

            self.event_publisher

        )


        self.dispatcher.register(

            "animal_health_review",

            animal_health_handler.handle,

        )



        #
        # Animal operational review commands
        #

        animal_review_handler = (
            AnimalOperationalReviewHandler(
                self.event_publisher
            )
        )


        self.dispatcher.register(

            "animal_operational_review",

            animal_review_handler.handle,

        )


        return self.dispatcher
