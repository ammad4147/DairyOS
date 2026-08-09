from dairyos.operations.resilience.models.operational_exception import (
    OperationalException,
)


class OperationalExceptionRepository:
    """
    In-memory operational exception repository.

    Persistence can be introduced later without
    changing service behaviour.
    """


    def __init__(
        self,
    ):

        self.exceptions = []



    def save(
        self,
        exception: OperationalException,
    ):

        existing = next(
            (
                item
                for item in self.exceptions
                if item.exception_id
                == exception.exception_id
            ),
            None,
        )


        if existing:

            index = self.exceptions.index(
                existing
            )

            self.exceptions[index] = exception

        else:

            self.exceptions.append(
                exception
            )


        return exception



    def get(
        self,
        exception_id: str,
    ):

        return next(
            (
                item
                for item in self.exceptions
                if item.exception_id
                == exception_id
            ),
            None,
        )



    def open_exceptions(
        self,
    ):

        return [
            item
            for item in self.exceptions
            if item.status == "open"
        ]



    def all(
        self,
    ):

        return list(
            self.exceptions
        )
