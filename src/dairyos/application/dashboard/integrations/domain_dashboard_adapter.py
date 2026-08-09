from dairyos.application.dashboard.models.milk_command import (
    MilkCommand,
)

from dairyos.farm.operations.runtime import (
    FarmOperationsRuntime,
)


class DomainDashboardAdapter:
    """
    Dashboard read adapter.

    Bridges operational runtime data and animal intelligence
    projections.

    Read side only.
    """

    def __init__(
        self,
        operations_runtime: FarmOperationsRuntime | None = None,
        animal_repository=None,
        operations_service=None,
        milk_repository=None,
        feed_repository=None,
        animal_bridge=None,
        animal_intelligence_service=None,
    ):

        self.operations_runtime = (
            operations_runtime
            if operations_runtime is not None
            else FarmOperationsRuntime(
                milk_repository=milk_repository,
                feed_repository=feed_repository,
            )
        )

        self.operations_service = (
            operations_service
        )

        self.animal_repository = (
            animal_repository
        )

        self.animal_bridge = (
            animal_bridge
        )

        self.animal_intelligence_service = (
            animal_intelligence_service
        )

    def _milk_records(self):

        repository = (
            self.operations_runtime
            .milk_repository
        )

        if hasattr(repository, "list_milk"):
            return repository.list_milk()

        if hasattr(repository, "get_all"):
            return repository.get_all()

        return []

    def _animal_records(self):

        if self.animal_repository is None:
            return []

        if hasattr(
            self.animal_repository,
            "get_all",
        ):
            return self.animal_repository.get_all()

        if hasattr(
            self.animal_repository,
            "list_animals",
        ):
            return self.animal_repository.list_animals()

        return []

    def get_milk_total(self):

        if self.operations_service:

            return (
                self.operations_service
                .daily_milk_total()
            )

        return sum(
            getattr(
                record,
                "litres",
                0.0,
            )
            for record in self._milk_records()
        )

    def get_milk_command(self):

        today_litres = (
            self.get_milk_total()
        )

        milking_animals = (
            self.get_milking_animals()
        )

        average = (
            today_litres / milking_animals
            if milking_animals > 0
            else 0.0
        )

        return MilkCommand(
            today_litres=today_litres,
            milking_animals=milking_animals,
            average_litres_per_animal=average,
            production_status=(
                "ACTIVE"
                if today_litres > 0
                else "NO_DATA"
            ),
        )

    def get_feed_consumption(self):

        if self.operations_service:

            return (
                self.operations_service
                .daily_feed_quantity()
            )

        repository = (
            self.operations_runtime
            .feed_repository
        )

        if hasattr(repository, "get_all"):
            records = repository.get_all()
        elif hasattr(repository, "list_feed"):
            records = repository.list_feed()
        else:
            records = []

        return sum(
            getattr(
                record,
                "quantity_kg",
                0.0,
            )
            for record in records
        )

    def get_total_animals(self):

        return len(
            self._animal_records()
        )

    def get_milking_animals(self):

        return sum(
            1
            for animal in self._animal_records()
            if (
                getattr(
                    animal,
                    "is_milking",
                    False,
                )
                or
                getattr(
                    animal,
                    "is_currently_milking",
                    False,
                )
            )
        )

    def get_dry_animals(self):

        return max(
            self.get_total_animals()
            -
            self.get_milking_animals(),
            0,
        )

    def get_pending_tasks(self):

        if self.operations_service:

            return (
                self.operations_service
                .breeding_pending_count()
            )

        return 0

    def get_overdue_tasks(self):

        return 0

    def get_animal_attention_count(self):

        return len(
            self.get_animal_attention_items()
        )

    def get_animal_attention_items(self):

        if self.animal_intelligence_service:

            result = (
                self.animal_intelligence_service
                .evaluate_all()
            )

            return result

        if self.animal_bridge is None:

            return []

        items = []

        for state in (
            self.animal_bridge
            .get_all_states()
        ):

            if state.attention_required:

                items.append(
                    {
                        "animal_id":
                            state.animal_id,

                        "reasons":
                            state.attention_reason,

                        "milk_deviation":
                            state.milk_deviation_percentage,
                    }
                )

        return items
