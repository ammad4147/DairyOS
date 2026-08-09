from dairyos.intelligence.knowledge.repository.lesson_repository import (
    LessonRepository,
)


class MemoryLessonRepository(
    LessonRepository,
):

    def __init__(
        self,
    ):

        self._items = []


    def save(
        self,
        lesson,
    ):

        self._items.append(
            lesson
        )


    def get_all(
        self,
    ):

        return self._items
