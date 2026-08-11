from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)


class ExecutionEventBridge:
    """
    Translates execution lifecycle domain events
    into enterprise OperationalEvents.

    Execution lifecycle remains a domain concern.

    OperationalEvent is the enterprise integration
    boundary.

    Contract guarantees:

    - invalid events raise ValueError
    - event.name becomes OperationalEvent.event_type
    - execution_id becomes OperationalEvent.entity_id
    - entity_type is always ``execution``
    - payload is copied rather than shared
    - actor is resolved from the lifecycle payload
    - missing execution identifiers fail explicitly
    """

    _ACTOR_FIELDS = (
        "completed_by",
        "verified_by",
        "started_by",
        "acknowledged_by",
        "assigned_to",
    )

    def adapt(
        self,
        event,
    ) -> OperationalEvent:
        """
        Adapt one execution lifecycle domain event
        into an enterprise OperationalEvent.

        The execution domain event remains authoritative.
        This bridge performs translation only.
        """

        if event is None:
            raise ValueError(
                "Execution event is required."
            )

        event_name = getattr(
            event,
            "name",
            None,
        )

        if not event_name:
            raise ValueError(
                "Execution event must contain a name."
            )

        raw_payload = getattr(
            event,
            "payload",
            None,
        )

        if not isinstance(
            raw_payload,
            dict,
        ):
            raise ValueError(
                "Execution event must contain a payload dictionary."
            )

        payload = dict(
            raw_payload
        )

        execution_id = payload.get(
            "execution_id"
        )

        if execution_id is None:
            raise ValueError(
                "Execution event must contain execution_id."
            )

        execution_id = str(
            execution_id
        )

        actor = self._resolve_actor(
            payload
        )

        return OperationalEvent(
            event_type=str(
                event_name
            ),
            entity_type="execution",
            entity_id=execution_id,
            actor=actor,
            payload=payload,
        )

    @classmethod
    def _resolve_actor(
        cls,
        payload: dict,
    ) -> str:
        """
        Resolve the attributable actor from the
        execution lifecycle payload.

        Lifecycle-specific attribution takes precedence
        over the generic SYSTEM fallback.
        """

        for field_name in cls._ACTOR_FIELDS:
            actor = payload.get(
                field_name
            )

            if actor:
                return str(
                    actor
                )

        return "SYSTEM"
