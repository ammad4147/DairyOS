from dairyos.intelligence.knowledge.models.knowledge_record import (
    KnowledgeRecord,
)

from dairyos.intelligence.knowledge.repository.adapters.memory_knowledge_record_repository import (
    MemoryKnowledgeRecordRepository,
)



def test_repository_save():

    repository = MemoryKnowledgeRecordRepository()

    record = KnowledgeRecord(
        knowledge_type="test",
        content="knowledge",
        source="unit",
        confidence=1.0,
    )

    repository.save(
        record
    )

    assert len(
        repository.get_all()
    ) == 1



def test_repository_returns_saved_record():

    repository = MemoryKnowledgeRecordRepository()

    record = KnowledgeRecord(
        knowledge_type="test",
        content="knowledge",
        source="unit",
        confidence=1.0,
    )

    repository.save(
        record
    )

    assert repository.get_all()[0] == record
