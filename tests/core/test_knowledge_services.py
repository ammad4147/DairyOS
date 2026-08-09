from dairyos.intelligence.knowledge.services.knowledge_service import (
    KnowledgeService,
)

from dairyos.intelligence.knowledge.repository.adapters.memory_knowledge_record_repository import (
    MemoryKnowledgeRecordRepository,
)

from dairyos.intelligence.knowledge.services.pattern_discovery_service import (
    PatternDiscoveryService,
)

from dairyos.intelligence.knowledge.services.rule_generation_service import (
    RuleGenerationService,
)

from dairyos.intelligence.knowledge.services.lesson_management_service import (
    LessonManagementService,
)



def test_knowledge_service_create():

    repository = MemoryKnowledgeRecordRepository()

    service = KnowledgeService(
        repository
    )

    record = service.create(
        "lesson",
        "monitor feed",
        "system",
        0.9,
    )

    assert record.content == "monitor feed"



def test_pattern_discovery_service():

    service = PatternDiscoveryService()

    pattern = service.discover(
        "production",
        "milk increase",
        10,
        0.8,
    )

    assert pattern.frequency == 10



def test_rule_generation_service():

    service = RuleGenerationService()

    rule = service.generate(
        "herd",
        "low yield",
        "inspect",
        0.7,
    )

    assert rule.action == "inspect"



def test_lesson_management_service():

    service = LessonManagementService()

    lesson = service.create(
        "farm",
        "check feed",
        "better production",
        0.8,
    )

    assert lesson.lesson == "check feed"
