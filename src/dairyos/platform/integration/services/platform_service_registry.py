from typing import Dict

from dairyos.platform.integration.models.platform_service import (
    PlatformService,
)


class PlatformServiceRegistry:
    """
    Central registry for enterprise services.
    """

    def __init__(self):

        self._services: Dict[str, PlatformService] = {}


    def register(
        self,
        service: PlatformService,
    ):

        self._services[
            service.name
        ] = service



    def get(
        self,
        name: str,
    ):

        return self._services.get(name)



    def list_services(self):

        return list(
            self._services.values()
        )



    def active_services(self):

        return [
            service
            for service in self._services.values()
            if service.enabled
        ]
