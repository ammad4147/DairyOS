from datetime import datetime, timezone
from typing import Dict

from dairyos.operations.events.operational_event import (
    OperationalEvent,
)

from dairyos.operations.intelligence.models.operational_signal import (
    OperationalSignal,
)

from .operations_intelligence_service import (
    OperationsIntelligenceService,
)


class OperationalEventSignalService:
    """
    Converts operational events into intelligence signals.
    """

    def __init__(
        self,
        intelligence_service: OperationsIntelligenceService,
    ):

        self.intelligence_service = (
            intelligence_service
        )

        self.signal_counter = 0


    def process_event(
        self,
        event: OperationalEvent,
    ) -> OperationalSignal:

        self.signal_counter += 1

        category, severity = (
            self._classify_event(
                event.event_type
            )
        )

        signal = OperationalSignal(

            signal_id=f"SIG-{self.signal_counter:04d}",

            category=category,

            description=(
                f"{event.event_type} "
                f"recorded for "
                f"{event.entity_id or event.farm_id}"
            ),

            severity=severity,

            source="OPERATIONAL_EVENT_ENGINE",

            created_at=(
                event.timestamp
                if event.timestamp
                else datetime.now(
                    timezone.utc
                )
            ),
        )


        self.intelligence_service.register_signal(
            signal
        )


        return signal



    def _classify_event(
        self,
        event_type: str,
    ) -> tuple[str, str]:

        rules: Dict[str, tuple[str, str]] = {

            "milking": (
                "PRODUCTION",
                "LOW",
            ),

            "feeding": (
                "FEEDING",
                "LOW",
            ),

            "health_alert": (
                "HEALTH",
                "HIGH",
            ),

            "task_delayed": (
                "EXECUTION",
                "HIGH",
            ),

            "task_completed": (
                "EXECUTION",
                "LOW",
            ),

        }


        return rules.get(
            event_type.lower(),
            (
                "GENERAL_OPERATION",
                "LOW",
            ),
        )
