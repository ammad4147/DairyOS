from ..database.models.operational_event_model import (
    OperationalEventModel,
)


class OperationalEventRepository:
    """
    Persistence boundary for enterprise operational events.

    Accepts the canonical OperationalEvent model and retains
    compatibility with legacy FarmOperationEvent callers.
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

    def _event_type(self, event):
        return self._value(
            event,
            "event_type",
            "name",
            "UNKNOWN_EVENT",
        )

    def _entity_type(self, event):
        return self._value(
            event,
            "entity_type",
            default="FARM",
        )

    def _entity_id(self, event):
        return self._value(
            event,
            "entity_id",
            "animal_id",
        )

    def _actor(self, event):
        return self._value(
            event,
            "actor",
            "operator",
        )

    def _timestamp(self, event):
        timestamp = getattr(
            event,
            "timestamp",
            None,
        )

        if timestamp is None:
            raise ValueError(
                "Operational event requires a timestamp."
            )

        return timestamp

    def _source(self, event):
        source = getattr(
            event,
            "source",
            None,
        )

        if source:
            return source

        entity_type = self._entity_type(
            event
        )

        if entity_type:
            return str(
                entity_type
            )

        return "FARM_OPERATIONS"

    def _build_description(self, event):
        description = self._event_type(
            event
        )

        entity_type = self._entity_type(
            event
        )

        entity_id = self._entity_id(
            event
        )

        actor = self._actor(
            event
        )

        if entity_type:
            description += (
                f" entity_type={entity_type}"
            )

        if entity_id:
            description += (
                f" entity_id={entity_id}"
            )

        if actor:
            description += (
                f" actor={actor}"
            )

        payload = getattr(
            event,
            "payload",
            None,
        )

        if payload:
            description += (
                f" payload={payload}"
            )

        return description

    def _to_model(self, event):
        timestamp = self._timestamp(
            event
        )

        if getattr(
            timestamp,
            "tzinfo",
            None,
        ) is not None:
            timestamp = timestamp.replace(
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

    def add(self, event):
        if event is None:
            raise ValueError(
                "Operational event is required."
            )

        if self.session:
            model = self._to_model(
                event
            )

            self.session.add(
                model
            )

            self.session.commit()

            return model

        self.records.append(
            event
        )

        return event

    def get_all(self):
        if self.session:
            return (
                self.session.query(
                    OperationalEventModel
                )
                .all()
            )

        return list(
            self.records
        )

    def count(self):
        if self.session:
            return (
                self.session.query(
                    OperationalEventModel
                )
                .count()
            )

        return len(
            self.records
        )
