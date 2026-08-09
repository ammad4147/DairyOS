from datetime import datetime, timezone

from dairyos.domain.commands import Command
from dairyos.data.models.animal import Animal


class AnimalManagementService:
    """
    Enterprise animal management boundary.

    Responsibilities:

    - register animals
    - retrieve animal records
    - maintain animal lifecycle operations
    - publish operational commands

    API layers must not directly mutate
    operational state projections.
    """

    def __init__(
        self,
        repository=None,
        operations=None,
    ):

        self.repository = repository

        self.operations = operations



    def register(
        self,
        payload: dict,
    ):

        animal_id = payload.get(
            "animal_id"
        )

        if not animal_id:
            raise ValueError(
                "animal_id required"
            )


        animal = Animal(
            animal_id=animal_id,
            **{
                key: value
                for key, value in payload.items()
                if key != "animal_id"
            },
        )


        if self.repository:

            self.repository.save(
                animal
            )


        if self.operations:

            return (
                self.operations.handle_command(
                    Command(
                        name="CreateAnimal",
                        payload={
                            **payload,
                            "active": True,
                            "created_at":
                                datetime.now(
                                    timezone.utc
                                ).isoformat(),
                        },
                    )
                )
            )


        return animal



    def get(
        self,
        animal_id: str,
    ):

        if self.repository:

            return (
                self.repository.get_by_animal_id(
                    animal_id
                )
            )

        return None



    def list_all(
        self,
    ):

        if self.repository:

            return (
                self.repository.get_all()
            )

        return []



    def exists(
        self,
        animal_id: str,
    ):

        return (
            self.get(animal_id)
            is not None
        )



    def update_milking_frequency(
        self,
        animal_id: str,
        frequency: str,
        changed_by=None,
        reason=None,
    ):

        animal = self.get(
            animal_id
        )

        if animal is None:

            raise ValueError(
                "Animal not found"
            )


        if hasattr(
            animal,
            "milking_frequency",
        ):

            animal.milking_frequency = (
                frequency
            )


        return animal