from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)


class ExecutionFarmEventAdapter:
    """
    Compatibility adapter from execution domain events to the
    farm-operation event boundary.

    Architectural contract:

        Execution domain event
                |
                v
        ExecutionFarmEventAdapter
                |
                v
        FarmOperationEvent

    The adapter is intentionally thin.

    It does not:
    - own execution state
    - mutate execution objects
    - publish events
    - perform lifecycle transitions
    - invoke subscribers
    - duplicate execution lifecycle rules

    The authoritative execution lifecycle path remains:

        ExecutionTrackingService
                |
                v
        ExecutionEventBridge
                |
                v
        OperationalEvent
                |
                v
        ExecutionEventSubscriber
                |
                v
        ExecutionLifecycleEventHandler
                |
                v
        ExecutionLifecycleBridge
    """

    SYSTEM_OPERATOR = "SYSTEM"

    ACTOR_FIELDS = (
        "completed_by",
        "verified_by",
        "started_by",
        "acknowledged_by",
        "assigned_to",
    )

    def adapt(self, event) -> FarmOperationEvent:
        """
        Convert an execution domain event into a FarmOperationEvent.

        Event payload is copied so the source event is never mutated.

        Execution events do not currently carry an animal identity at
        this boundary, therefore animal_id remains None.
        """

        if event is None:
            raise ValueError(
                "ExecutionFarmEventAdapter requires an event"
            )

        event_name = getattr(event, "name", None)

        if not event_name:
            raise ValueError(
                "Execution event requires name"
            )

        raw_payload = getattr(event, "payload", None)

        if raw_payload is None:
            payload = {}
        else:
            try:
                payload = dict(raw_payload)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "Execution event payload must be mapping-compatible"
                ) from exc

        operator = self._resolve_operator(payload)

        return FarmOperationEvent(
            event_type=event_name,
            animal_id=None,
            operator=operator,
            payload=payload,
        )

    @classmethod
    def _resolve_operator(cls, payload: dict) -> str:
        """
        Resolve the attributable actor from the execution event payload.

        The first populated actor field wins. SYSTEM is used only when
        the execution event contains no attributable actor.
        """

        for field_name in cls.ACTOR_FIELDS:
            value = payload.get(field_name)

            if value is not None and str(value).strip():
                return str(value)

        return cls.SYSTEM_OPERATOR
