from dairyos.intelligence.learning_feedback.models.learning_feedback import (
    LearningFeedback,
)

from dairyos.intelligence.learning_feedback.models.learning_event import (
    LearningEvent,
)

from dairyos.intelligence.learning_feedback.models.knowledge_adjustment import (
    KnowledgeAdjustment,
)

from dairyos.intelligence.learning_feedback.models.learning_score import (
    LearningScore,
)

from dairyos.intelligence.learning_feedback.models.learning_memory import (
    LearningMemory,
)


def test_learning_feedback_creation():

    item = LearningFeedback(
        decision_type="feed_adjustment",
        workflow_type="daily_operation",
        execution_result="completed",
        success=True,
        feedback="Improved yield",
    )

    assert item.success is True



def test_learning_event_creation():

    event = LearningEvent(
        event_type="analysis",
        source="execution",
        description="success",
    )

    assert event.source == "execution"



def test_knowledge_adjustment_creation():

    item = KnowledgeAdjustment(
        decision_area="feeding",
        previous_value="100",
        new_value="110",
        reason="better output",
    )

    assert item.new_value == "110"



def test_learning_score_creation():

    score = LearningScore(
        decision_type="milking",
        accuracy_score=0.9,
        execution_score=0.8,
        confidence_score=0.85,
    )

    assert score.accuracy_score == 0.9



def test_learning_memory_creation():

    memory = LearningMemory(
        category="feed",
        pattern="higher intake",
        frequency=5,
        confidence=0.8,
    )

    assert memory.frequency == 5
