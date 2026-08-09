from dairyos.intelligence.learning_feedback.repository.adapters.memory_learning_feedback_repository import (
    MemoryLearningFeedbackRepository,
)

from dairyos.intelligence.learning_feedback.services.learning_feedback_service import (
    LearningFeedbackService,
)

from dairyos.intelligence.learning_feedback.services.learning_analyzer import (
    LearningAnalyzer,
)

from dairyos.intelligence.learning_feedback.services.knowledge_updater import (
    KnowledgeUpdater,
)

from dairyos.intelligence.learning_feedback.services.learning_scorer import (
    LearningScorer,
)


def test_feedback_service_capture():

    service = LearningFeedbackService(
        MemoryLearningFeedbackRepository()
    )

    result = service.capture(
        "decision",
        "workflow",
        "success",
        True,
        "good",
    )

    assert result.success is True



def test_learning_analyzer():

    analyzer = LearningAnalyzer()

    event = analyzer.analyze(
        type(
            "Feedback",
            (),
            {
                "success": True,
                "workflow_type": "test",
            },
        )()
    )

    assert event.event_type == "execution_analysis"



def test_knowledge_update():

    updater = KnowledgeUpdater()

    result = updater.update(
        "feed",
        "old",
        "new",
        "reason",
    )

    assert result.new_value == "new"



def test_learning_score():

    scorer = LearningScorer()

    result = scorer.score(
        "decision",
        0.9,
        0.8,
        0.85,
    )

    assert result.confidence_score == 0.85
