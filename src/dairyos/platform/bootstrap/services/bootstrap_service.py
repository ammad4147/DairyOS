from dairyos.platform.bootstrap.platform_container import (
    PlatformContainer,
)



class BootstrapService:
    """
    Enterprise platform startup service.
    """



    def initialize(self):

        return PlatformContainer()
