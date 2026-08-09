class LessonRepository:
    """
    Repository interface for operational lessons.
    """


    def save(
        self,
        lesson,
    ):

        raise NotImplementedError


    def get_all(
        self,
    ):

        raise NotImplementedError
