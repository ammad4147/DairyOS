from dairyos.farm.operations.repositories.adapters.memory_milk_repository import (
    MemoryMilkRepository,
)

from dairyos.farm.operations.repositories.adapters.memory_feed_repository import (
    MemoryFeedRepository,
)

from dairyos.farm.operations.repositories.adapters.memory_health_repository import (
    MemoryHealthRepository,
)

from dairyos.farm.operations.repositories.adapters.memory_breeding_repository import (
    MemoryBreedingRepository,
)


class FarmOperationsService:
    """
    Provides operational summaries
    from actual farm records.

    This service connects:
    farm activity -> operational intelligence -> management view.
    """


    def __init__(
        self,
        milk_repository=None,
        feed_repository=None,
        health_repository=None,
        breeding_repository=None,
    ):

        self.milk_repository = (
            milk_repository
            if milk_repository
            else MemoryMilkRepository()
        )

        self.feed_repository = (
            feed_repository
            if feed_repository
            else MemoryFeedRepository()
        )

        self.health_repository = (
            health_repository
            if health_repository
            else MemoryHealthRepository()
        )

        self.breeding_repository = (
            breeding_repository
            if breeding_repository
            else MemoryBreedingRepository()
        )


    def daily_milk_total(
        self,
    ):

        return sum(
            record.litres
            for record in self.milk_repository.get_all()
        )


    def daily_feed_quantity(
        self,
    ):

        return sum(
            record.quantity_kg
            for record in self.feed_repository.get_all()
        )


    def daily_feed_cost(
        self,
    ):

        return sum(
            record.cost
            for record in self.feed_repository.get_all()
        )


    def health_attention_count(
        self,
    ):

        return len(
            self.health_repository.get_all()
        )


    def breeding_pending_count(
        self,
    ):

        return len(
            self.breeding_repository.get_all()
        )


    def attention_items(
        self,
    ):
        """
        Returns operational items requiring attention.
        """

        items = []

        for observation in self.health_repository.get_all():

            items.append(
                {
                    "type": "health",
                    "animal_id": observation.animal_id,
                    "issue": observation.observation_type,
                    "notes": observation.notes,
                    "operator": observation.operator,
                }
            )

        return items
