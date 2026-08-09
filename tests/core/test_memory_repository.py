from dairyos.intelligence.memory.repository.adapters.memory_memory_repository import (
    MemoryMemoryRepository,
)

from dairyos.intelligence.memory.repository.adapters.memory_context_repository import (
    MemoryContextRepository,
)

from dairyos.intelligence.memory.repository.adapters.memory_snapshot_repository import (
    MemorySnapshotRepository,
)


def test_memory_repository_save():

    repository = MemoryMemoryRepository()

    item = "memory"

    repository.save(
        item
    )

    assert repository.get_all()[0] == item



def test_context_repository_save():

    repository = MemoryContextRepository()

    item = "context"

    repository.save(
        item
    )

    assert repository.get_all()[0] == item



def test_snapshot_repository_save():

    repository = MemorySnapshotRepository()

    item = "snapshot"

    repository.save(
        item
    )

    assert repository.get_all()[0] == item
