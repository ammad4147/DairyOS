from ..models.knowledge_pattern import KnowledgePattern


class PatternLearningService:
    """
    Converts operational feedback into reusable patterns.
    """

    def create_pattern(
        self,
        category: str,
        situation: str,
        response: str,
        confidence: float = 0.5,
    ):

        return KnowledgePattern(
            category=category,
            situation=situation,
            successful_response=response,
            confidence=confidence,
        )

