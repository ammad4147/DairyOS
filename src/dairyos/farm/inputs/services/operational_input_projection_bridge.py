from dairyos.domain.events.operational_input_received import (
    OperationalInputReceived,
)

from dairyos.domain.events import Event

from dairyos.farm.inputs.models.operational_projection_event import (
    OperationalProjectionEvent,
)


class OperationalInputProjectionBridge:
    """
    Converts canonical OperationalInputReceived events into the
    vocabulary required by FarmOperationalState.

    The canonical operational-input contract remains authoritative.
    This bridge is the translation boundary between:

        canonical input vocabulary
            ->
        operational-state projection vocabulary

    Canonical fields are preserved. Projection-specific aliases are
    added only where the operational-state contract requires them.

    The bridge accepts:
        1. real OperationalInputReceived events;
        2. persisted domain Event instances named
           "OperationalInputReceived";
        3. canonical event-shaped objects exposing a dict payload.

    The third form is intentional compatibility with the canonical
    event contract tests and lightweight event adapters.
    """

    EVENT_MAP = {
        "milk_production": "milk_recorded",
        "feeding": "feed_recorded",
        "animal_health": "health_recorded",
        "breeding": "breeding_recorded",
        "workforce": "workforce_activity_recorded",
        "inventory": "inventory_status_recorded",
        "equipment": "equipment_status_recorded",
        "financial": "financial_status_recorded",
    }

    _ENVELOPE_FIELDS = {
        "input_type",
        "source",
        "actor",
    }

    def __init__(self, state_service):
        self.state_service = state_service

    @classmethod
    def _business_payload(cls, payload):
        """
        Return canonical business fields without the generic
        operational-input envelope.

        The original canonical payload is never mutated.
        """
        if not isinstance(payload, dict):
            return {}

        return {
            key: value
            for key, value in payload.items()
            if key not in cls._ENVELOPE_FIELDS
        }

    @classmethod
    def _project_payload(cls, input_type, payload):
        """
        Translate canonical input vocabulary into operational-state
        projection vocabulary while preserving canonical fields.
        """
        projected = dict(payload)

        if input_type == "milk_production":
            session = payload.get("milking_session")

            if session is not None:
                projected.setdefault("session", session)
                projected.setdefault("shift", session)

            if "total_yield" in payload:
                projected.setdefault(
                    "litres",
                    payload["total_yield"],
                )

        elif input_type == "workforce":
            worker_id = payload.get("worker_id")
            activity = payload.get("activity")

            if worker_id is not None:
                projected.setdefault(
                    "metric_type",
                    worker_id,
                )

            if activity is not None:
                projected.setdefault(
                    "value",
                    activity,
                )

        elif input_type == "inventory":
            item = payload.get("item")

            if item is not None:
                projected.setdefault(
                    "inventory_type",
                    item,
                )

            projected.setdefault(
                "details",
                cls._business_payload(payload),
            )

        elif input_type == "equipment":
            equipment_id = payload.get("equipment_id")

            if equipment_id is not None:
                projected.setdefault(
                    "equipment_id",
                    equipment_id,
                )

            projected.setdefault(
                "details",
                cls._business_payload(payload),
            )

        elif input_type == "financial":
            transaction_type = payload.get(
                "transaction_type"
            )

            if transaction_type is not None:
                projected.setdefault(
                    "financial_type",
                    transaction_type,
                )

            projected.setdefault(
                "details",
                cls._business_payload(payload),
            )

        return projected

    @staticmethod
    def _extract_payload(event):
        """
        Extract the canonical operational-input payload.

        Real OperationalInputReceived events, persisted Event instances,
        and canonical event-shaped adapters are supported.

        Returning None means the supplied object is not an operational
        input event.
        """
        if isinstance(event, OperationalInputReceived):
            return event.payload

        if (
            isinstance(event, Event)
            and event.name == "OperationalInputReceived"
        ):
            return event.payload

        payload = getattr(event, "payload", None)

        if isinstance(payload, dict):
            return payload

        return None

    def project(self, event):
        """
        Project a supported operational-input event.

        Unsupported events are ignored.

        The canonical input vocabulary is read from payload["input_type"].
        """
        payload = self._extract_payload(event)

        if not isinstance(payload, dict):
            return None

        input_type = payload.get("input_type")

        projection_event_type = self.EVENT_MAP.get(
            input_type
        )

        if not projection_event_type:
            return None

        projected_payload = self._project_payload(
            input_type,
            payload,
        )

        projection_event = OperationalProjectionEvent(
            event_type=projection_event_type,
            payload=projected_payload,
            operator=payload.get("actor"),
        )

        self.state_service.handle(
            projection_event
        )

        return projection_event
