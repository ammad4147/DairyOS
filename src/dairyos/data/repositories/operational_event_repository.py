from datetime import datetime

from ..database.models.operational_event_model import (
    OperationalEventModel,
)


class OperationalEventRepository:
    """
    Persistence boundary for enterprise operational events.

    The repository accepts the canonical OperationalEvent contract while
    retaining compatibility with legacy FarmOperationEvent callers.

    The current database schema stores:

        event_type
        source
        description
        created_at

    Until a schema migration introduces dedicated entity/actor/payload
    columns, those values are encoded deterministically in description.

    The repository owns persistence concerns only. It does not publish,
    dispatch, or apply business rules.
    """

    def __init__(
        self,
        session=None,
    ):
        self.session = session
        self.records = []

    @staticmethod
    def _value(
        event,
        primary,
        fallback=None,
        default=None,
    ):
        value = getattr(
            event,
            primary,
            None,
        )

        if value is not None:
            return value

        if fallback is not None:
            value = getattr(
                event,
                fallback,
                None,
            )

            if value is not None:
                return value

        return default

    def _event_type(
        self,
        event,
    ):
        return str(
            self._value(
                event,
                "event_type",
                "name",
                "UNKNOWN_EVENT",
            )
        )

    def _entity_type(
        self,
        event,
    ):
        value = self._value(
            event,
            "entity_type",
            default="FARM",
        )

        return (
            str(value)
            if value is not None
            else "FARM"
        )

    def _entity_id(
        self,
        event,
    ):
        value = self._value(
            event,
            "entity_id",
            "animal_id",
        )

        return (
            str(value)
            if value is not None
            else None
        )

    def _actor(
        self,
        event,
    ):
        value = self._value(
            event,
            "actor",
            "operator",
        )

        return (
            str(value)
            if value is not None
            else None
        )

    def _payload(
        self,
        event,
    ):
        payload = getattr(
            event,
            "payload",
            None,
        )

        if payload is None:
            return None

        if isinstance(
            payload,
            dict,
        ):
            return dict(
                payload
            )

        return payload

    def _timestamp(
        self,
        event,
    ):
        timestamp = getattr(
            event,
            "timestamp",
            None,
        )

        if timestamp is None:
            raise ValueError(
                "Operational event requires a timestamp."
            )

        if not isinstance(
            timestamp,
            datetime,
        ):
            raise TypeError(
                "Operational event timestamp must be a datetime."
            )

        return timestamp

    def _source(
        self,
        event,
    ):
        source = getattr(
            event,
            "source",
            None,
        )

        if source:
            return str(
                source
            )

        entity_type = self._entity_type(
            event
        )

        if entity_type:
            return entity_type

        return "FARM_OPERATIONS"

    def _build_description(
        self,
        event,
    ):
        parts = [
            self._event_type(
                event
            )
        ]

        entity_type = self._entity_type(
            event
        )

        entity_id = self._entity_id(
            event
        )

        actor = self._actor(
            event
        )

        payload = self._payload(
            event
        )

        if entity_type:
            parts.append(
                f"entity_type={entity_type}"
            )

        if entity_id:
            parts.append(
                f"entity_id={entity_id}"
            )

        if actor:
            parts.append(
                f"actor={actor}"
            )

        if payload:
            parts.append(
                f"payload={payload}"
            )

        return " ".join(
            parts
        )

    def _to_model(
        self,
        event,
    ):
        timestamp = self._timestamp(
            event
        )

        if timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone().replace(
                tzinfo=None
            )

        return OperationalEventModel(
            event_type=self._event_type(
                event
            ),
            source=self._source(
                event
            ),
            description=self._build_description(
                event
            ),
            created_at=timestamp,
        )

    def add(
        self,
        event,
    ):
        if event is None:
            raise ValueError(
                "Operational event is required."
            )

        if self.session is None:
            self.records.append(
                event
            )

            return event

        model = self._to_model(
            event
        )

        self.session.add(
            model
        )

        self.session.commit()

        return model

    def get_all(
        self,
    ):
        if self.session is None:
            return list(
                self.records
            )

        return list(
            self.session.query(
                OperationalEventModel
            )
            .order_by(
                OperationalEventModel.created_at.asc(),
                OperationalEventModel.id.asc(),
            )
            .all()
        )

    def count(
        self,
    ):
        if self.session is None:
            return len(
                self.records
            )

        return (
            self.session.query(
                OperationalEventModel
            )
            .count()
        )
