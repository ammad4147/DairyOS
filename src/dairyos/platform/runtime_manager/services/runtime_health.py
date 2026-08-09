from dataclasses import dataclass

from dairyos.platform.runtime_manager.services.runtime_manager import (
    RuntimeManager,
)


@dataclass
class RuntimeHealth:
    """
    Runtime health snapshot.
    """

    running: bool

    active_services: int


class RuntimeHealthService:
    """
    Provides runtime health information.
    """

    def check(
        self,
        runtime_manager: RuntimeManager,
    ):

        state = runtime_manager.status()

        return RuntimeHealth(
            running=state.status.value == "running",
            active_services=state.active_services,
        )
