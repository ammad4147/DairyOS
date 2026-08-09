from dairyos.platform.runtime.models.platform_runtime_state import (
    PlatformRuntimeState
)


class PlatformRuntime:
    """
    Enterprise platform runtime coordinator.

    Provides a controlled execution boundary
    for platform services.
    """

    def __init__(self):
        self.state = PlatformRuntimeState(
            runtime_id="default-runtime"
        )

    def start(self):
        self.state.active = True
        return self.state

    def stop(self):
        self.state.active = False
        return self.state

    def status(self) -> str:
        return (
            "RUNNING"
            if self.state.active
            else "STOPPED"
        )
