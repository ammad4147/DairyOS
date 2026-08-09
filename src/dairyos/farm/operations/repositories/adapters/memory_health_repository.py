from dairyos.farm.operations.repositories.health_repository import (
    HealthRepository,
)


class MemoryHealthRepository(
    HealthRepository,
):

    def __init__(
        self,
    ):

        self.records = []


    def save(
        self,
        observation,
    ):

        self.records.append(
            observation
        )

        return observation


    def get_all(
        self,
    ):

        return self.records
