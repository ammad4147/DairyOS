from dairyos.platform.runtime_manager.services.runtime_manager import (
    RuntimeManager,
)


class RuntimeOrchestrator:
    """
    Coordinates DairyOS enterprise runtime startup.
    """

    def __init__(
        self,
        runtime_manager: RuntimeManager,
        registry=None,
        bootstrap=None,
    ):
        self.runtime_manager = runtime_manager
        self.registry = registry
        self.bootstrap = bootstrap

    def start(self):

        if self.bootstrap:
            self.bootstrap.initialize()

        if self.registry:
            services = self.registry.list_services()

            for service in services:
                self.runtime_manager.register_component(
                    service
                )

        return self.runtime_manager.start()

    def stop(self):

        return self.runtime_manager.state.stop()
