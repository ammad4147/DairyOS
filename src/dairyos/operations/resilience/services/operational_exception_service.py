from dairyos.operations.resilience.models.operational_exception import (
    OperationalException,
)


class OperationalExceptionService:
    """
    Application service for operational exceptions.

    Records deviations without stopping operations.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def record_exception(
        self,
        category: str,
        description: str,
        severity: str,
        source: str,
    ):

        exception = OperationalException(

            category=category,

            description=description,

            severity=severity,

            source=source,

        )


        return self.repository.save(
            exception
        )



    def resolve_exception(
        self,
        exception_id: str,
    ):

        exception = (
            self.repository.get(
                exception_id
            )
        )


        if exception is None:

            return None


        exception.resolve()


        return self.repository.save(
            exception
        )



    def open_exceptions(
        self,
    ):

        return (
            self.repository.open_exceptions()
        )
