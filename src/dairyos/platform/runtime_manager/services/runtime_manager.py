"""Compatibility runtime manager for the legacy platform runtime API."""

from typing import Any

from dairyos.platform.runtime_manager.models.runtime_status import RuntimeState


class RuntimeManager:
    """Track registered runtime components and their aggregate lifecycle."""

    def __init__(self) -> None:
        self.state = RuntimeState()
        self._components: list[Any] = []

    def register_component(self, component: Any) -> Any:
        """Register one component and return it for composition chaining."""
        if component is None:
            raise ValueError("Runtime component is required.")
        self._components.append(component)
        return component

    def start(self) -> RuntimeState:
        """Start the manager and count only enabled components."""
        active_services = sum(
            1
            for component in self._components
            if bool(getattr(component, "enabled", True))
        )
        self.state.start(active_services)
        return self.state

    def stop(self) -> RuntimeState:
        """Stop the manager and clear its active-service count."""
        self.state.stop()
        return self.state

    def status(self) -> RuntimeState:
        """Return the current runtime state without mutating it."""
        return self.state
