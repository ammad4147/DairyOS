from abc import ABC, abstractmethod

from dairyos.farm.operations.models.breeding_record import (
    BreedingRecord,
)


class BreedingRepository(ABC):
    """
    Repository boundary for breeding records.
    """


    @abstractmethod
    def save(
        self,
        record: BreedingRecord,
    ):
        pass


    @abstractmethod
    def get_all(
        self,
    ) -> list[BreedingRecord]:
        pass
