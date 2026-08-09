from dairyos.domain.events.operational_input_received import (
    OperationalInputReceived,
)

from dairyos.domain.events import Event


class OperationalProjectionEvent:
    """
    Internal projection event passed into
    FarmOperationalStateService.

    This is deliberately lightweight and does not introduce
    another persistent event model.
    """

    def __init__(
        self,
        event_type,
        payload,
        operator=None,
    ):
        self.event_type = event_type
        self.payload = payload
        self.operator = operator

        self.animal_id = (
            payload.get("animal_id")
            if isinstance(payload, dict)
            else None
        )


class OperationalInputProjectionBridge:
    """
    Converts OperationalInputReceived events into the
    FarmOperationalState projection vocabulary.

    Supported live input:

        OperationalInputReceived

    Supported persisted input:

        domain Event(name="OperationalInputReceived")
    """

    EVENT_MAP = {
        "milk_production":
            "milk_recorded",

        "feeding":
            "feed_recorded",

        "animal_health":
            "health_recorded",

        "breeding":
            "breeding_recorded",

        "workforce":
            "workforce_activity_recorded",

        "inventory":
            "inventory_status_recorded",

        "equipment":
            "equipment_status_recorded",

        "financial":
            "financial_status_recorded",
    }

    def __init__(self, state_service):
        self.state_service = state_service

    def project(self, event):
        """
        Project a supported operational-input event.

        Unsupported events are ignored.
        """

        payload = None

        if isinstance(
            event,
            OperationalInputReceived,
        ):
            payload = event.payload

        elif (
            isinstance(event, Event)
            and event.name == "OperationalInputReceived"
        ):
            payload = event.payload

        else:
            return None

        input_type = (
            payload.get("input_type")
            if isinstance(payload, dict)
            else None
        )

        projection_event_type = (
            self.EVENT_MAP.get(input_type)
        )

        if not projection_event_type:
            return None

        projection_event = OperationalProjectionEvent(
            event_type=projection_event_type,

            payload=payload,

            operator=(
                payload.get("actor")
                if isinstance(payload, dict)
                else None
            ),
        )

        self.state_service.handle(
            projection_event
        )

        return projection_event
