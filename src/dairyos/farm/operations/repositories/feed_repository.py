from abc import ABC, abstractmethod

from dairyos.farm.operations.models.feed_record import (
    FeedRecord,
)


class FeedRepository(ABC):
    """
    Repository boundary for feed records.
    """


    @abstractmethod
    def save(
        self,
        record: FeedRecord,
    ):
        pass


    @abstractmethod
    def get_all(
        self,
    ) -> list[FeedRecord]:
        pass
