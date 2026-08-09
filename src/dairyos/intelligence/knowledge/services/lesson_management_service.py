from dairyos.intelligence.knowledge.models.operational_lesson import (
    OperationalLesson,
)


class LessonManagementService:
    """
    Manages operational lessons.

    Future extensions:

    - lesson scoring
    - lesson recommendation
    """


    def create(
        self,
        source: str,
        lesson: str,
        impact: str,
        confidence: float,
    ) -> OperationalLesson:

        return OperationalLesson(
            source=source,
            lesson=lesson,
            impact=impact,
            confidence=confidence,
        )
