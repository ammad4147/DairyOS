from dairyos.platform.integration.services.platform_service_registry import (
    PlatformServiceRegistry,
)


class PlatformRegistrationService:
    """
    Registers enterprise platform capabilities.
    """

    def __init__(
        self,
        registry: PlatformServiceRegistry,
    ):

        self.registry = registry



    def register_service(
        self,
        name: str,
        service: object,
    ):

        from dairyos.platform.integration.models.platform_service import (
            PlatformService,
        )

        self.registry.register(
            PlatformService(
                name=name,
                service=service,
            )
        )


    def count(self):

        return len(
            self.registry.active_services()
        )
