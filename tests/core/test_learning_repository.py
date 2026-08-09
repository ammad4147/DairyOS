from dairyos.intelligence.learning_feedback.repository.adapters.memory_learning_feedback_repository import (
    MemoryLearningFeedbackRepository,
)

from dairyos.intelligence.learning_feedback.models.learning_feedback import (
    LearningFeedback,
)


def test_repository_save():

    repository = MemoryLearningFeedbackRepository()

    item = LearningFeedback(
        decision_type="test",
        workflow_type="workflow",
        execution_result="done",
        success=True,
        feedback="ok",
    )

    repository.save(item)

    assert len(repository.get_all()) == 1



def test_repository_returns_saved_feedback():

    repository = MemoryLearningFeedbackRepository()

    item = LearningFeedback(
        decision_type="test",
        workflow_type="workflow",
        execution_result="done",
        success=False,
        feedback="failed",
    )

    repository.save(item)

    assert repository.get_all()[0] == item
