from abc import ABC, abstractmethod


class SnapshotRepository(ABC):
    """
    Repository interface for memory snapshots.
    """


    @abstractmethod
    def save(
        self,
        snapshot,
    ):
        pass


    @abstractmethod
    def get_all(
        self,
    ):
        pass
