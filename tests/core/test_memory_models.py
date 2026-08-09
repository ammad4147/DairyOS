from dairyos.intelligence.memory.models.memory_record import (
    MemoryRecord,
)

from dairyos.intelligence.memory.models.memory_event import (
    MemoryEvent,
)

from dairyos.intelligence.memory.models.memory_context import (
    MemoryContext,
)

from dairyos.intelligence.memory.models.memory_snapshot import (
    MemorySnapshot,
)


def test_memory_record_creation():

    memory = MemoryRecord(
        memory_id="m1",
        memory_type="operational",
        content="test",
        source="system",
        confidence=0.9,
    )

    assert memory.memory_id == "m1"



def test_memory_event_creation():

    event = MemoryEvent(
        event_id="e1",
        event_type="created",
        description="memory created",
        source="system",
    )

    assert event.event_id == "e1"



def test_memory_context_creation():

    context = MemoryContext(
        context_id="c1",
        context_type="farm",
        description="test",
        owner="system",
    )

    assert context.context_id == "c1"



def test_memory_snapshot_creation():

    snapshot = MemorySnapshot(
        snapshot_id="s1",
        memory_count=10,
        description="snapshot",
        created_by="system",
    )

    assert snapshot.snapshot_id == "s1"
