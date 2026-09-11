"""Compatibility bridge from operational domains to the event bus."""

from typing import Any

from dairyos.domain.events import Event


class EventBridge:
    """Connect operational domains to the enterprise event bus."""

    def __init__(self, event_bus: Any) -> None:
        self.event_bus = event_bus

    def publish_domain_event(
        self,
        domain: str,
        event_name: str,
        payload: dict[str, Any],
    ) -> Any:
        event = Event(
            name=event_name,
            payload={
                "domain": domain,
                **payload,
            },
        )
        return self.event_bus.publish(event)
