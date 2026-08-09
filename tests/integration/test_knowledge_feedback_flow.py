"""
DairyOS Sprint 025

Knowledge Feedback Integration Validation

Learning Feedback
        ?
Knowledge
        ?
Operational Improvement
"""


def test_knowledge_feedback_components():

    from dairyos.intelligence.learning_feedback.gateway.learning_gateway import (
        LearningGateway,
    )

    from dairyos.intelligence.learning_feedback.services.learning_feedback_service import (
        LearningFeedbackService,
    )

    from dairyos.intelligence.knowledge.gateway.knowledge_gateway import (
        KnowledgeGateway,
    )

    from dairyos.intelligence.knowledge.services.knowledge_service import (
        KnowledgeService,
    )


    assert LearningGateway is not None
    assert LearningFeedbackService is not None
    assert KnowledgeGateway is not None
    assert KnowledgeService is not None
