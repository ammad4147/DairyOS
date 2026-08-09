# src/dairyos/alerts/engine.py
"""Simple alert engine – logs a warning and rebuilds the dashboard."""
import logging
from src.dairyos.runtime.container import RuntimeContainer
from src.dairyos.domain.events import Event

log = logging.getLogger(__name__)

class AlertEngine:
    def __init__(self, container: RuntimeContainer):
        self.container = container

    def handle_event(self, event: Event):
        if event.name == "MilkRecorded":
            qty = event.payload.get("quantity", 0)
            if qty < 1.0:
                log.warning(f"Low milk alert: {event.payload}")

        self.container.dashboard.rebuild()
