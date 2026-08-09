from abc import ABC, abstractmethod

from dairyos.farm.operations.models.milk_record import (
    MilkRecord,
)


class MilkRepository(ABC):
    """
    Repository boundary for milk records.

    Keeps operational services
    independent from storage.
    """


    @abstractmethod
    def save(
        self,
        record: MilkRecord,
    ):
        pass


    @abstractmethod
    def get_all(
        self,
    ) -> list[MilkRecord]:
        pass
