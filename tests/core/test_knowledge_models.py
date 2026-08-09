from dairyos.intelligence.knowledge.models.knowledge_pattern import (
    KnowledgePattern,
)

from dairyos.intelligence.knowledge.models.operational_lesson import (
    OperationalLesson,
)

from dairyos.intelligence.knowledge.models.knowledge_rule import (
    KnowledgeRule,
)

from dairyos.intelligence.knowledge.models.knowledge_record import (
    KnowledgeRecord,
)


def test_knowledge_pattern_creation():

    item = KnowledgePattern(
        category="feed",
        pattern="higher intake improves yield",
        frequency=5,
        confidence=0.9,
    )

    assert item.category == "feed"



def test_operational_lesson_creation():

    item = OperationalLesson(
        source="farm",
        lesson="monitor intake",
        impact="production improvement",
        confidence=0.8,
    )

    assert item.source == "farm"



def test_knowledge_rule_creation():

    item = KnowledgeRule(
        domain="herd",
        condition="low milk",
        action="inspect cow",
        confidence=0.7,
    )

    assert item.domain == "herd"



def test_knowledge_record_creation():

    item = KnowledgeRecord(
        knowledge_type="lesson",
        content="example",
        source="system",
        confidence=1.0,
    )

    assert item.knowledge_type == "lesson"
