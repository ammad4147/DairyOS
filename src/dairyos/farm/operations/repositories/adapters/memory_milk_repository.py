from dairyos.farm.operations.repositories.milk_repository import (
    MilkRepository,
)


class MemoryMilkRepository(
    MilkRepository,
):
    """
    In-memory milk storage.

    Used for:

    - testing
    - development
    - future adapter validation
    """


    def __init__(
        self,
    ):

        self.records = []


    def save(
        self,
        record,
    ):

        self.records.append(
            record
        )

        return record


    def get_all(
        self,
    ):

        return self.records
