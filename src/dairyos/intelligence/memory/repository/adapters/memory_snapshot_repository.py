from dairyos.intelligence.memory.repository.snapshot_repository import (
    SnapshotRepository,
)


class MemorySnapshotRepository(SnapshotRepository):
    """
    In-memory storage for memory snapshots.
    """


    def __init__(
        self,
    ):

        self.snapshots = []


    def save(
        self,
        snapshot,
    ):

        self.snapshots.append(
            snapshot
        )

        return snapshot


    def get_all(
        self,
    ):

        return self.snapshots
