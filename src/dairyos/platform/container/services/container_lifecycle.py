from dairyos.platform.container.services.dependency_container import (
    DependencyContainer,
)


class ContainerLifecycleManager:
    """
    Controls dependency container lifecycle.
    """

    def __init__(
        self,
        container: DependencyContainer,
    ):

        self.container = container


    def start(self):

        services = self.container.list_services()

        activated = []

        for service_name in services:

            instance = self.container.resolve(
                service_name
            )

            activated.append(
                instance
            )


        return {
            "started": True,
            "services": len(activated),
        }


    def stop(self):

        self.container._instances.clear()

        return {
            "stopped": True,
            "services": 0,
        }
