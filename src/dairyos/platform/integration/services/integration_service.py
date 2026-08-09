from ..models.integration_request import IntegrationRequest
from ..models.integration_result import IntegrationResult


class IntegrationService:
    """
    Enterprise platform coordination service.

    Provides a controlled boundary between
    independent DairyOS platform capabilities.
    """

    def __init__(self):
        self._handlers = {}

    def register_handler(
        self,
        service_name: str,
        handler
    ) -> None:
        """
        Register a platform service handler.
        """

        self._handlers[service_name] = handler

    def execute(
        self,
        request: IntegrationRequest
    ) -> IntegrationResult:
        """
        Execute integration request.
        """

        handler = self._handlers.get(
            request.target_service
        )

        if not handler:
            return IntegrationResult(
                success=False,
                message=(
                    f"No integration handler "
                    f"registered for {request.target_service}"
                )
            )

        result = handler(request)

        if isinstance(result, IntegrationResult):
            return result

        return IntegrationResult(
            success=True,
            data={
                "result": result
            }
        )
