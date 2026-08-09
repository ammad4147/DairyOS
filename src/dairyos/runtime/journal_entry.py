"""
Journal persistence record.

Sprint-038
==========

This is a persistence-boundary value object.

It is deliberately not part of the domain event package because
journal metadata belongs to event persistence rather than domain
business semantics.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class JournalEntry:
    """
    Immutable persistence representation of a domain event.
    """

    event_id: str

    event_type: str

    timestamp: datetime

    payload: dict[str, Any]

    @classmethod
    def from_event(
        cls,
        event,
    ) -> "JournalEntry":
        """
        Convert a domain event into its persistence representation.

        Existing event identity is preserved when the event exposes
        an event_id. Generic legacy Event instances receive a journal
        identity at this persistence boundary.
        """

        event_id = getattr(
            event,
            "event_id",
            None,
        )

        if not event_id:
            event_id = str(uuid4())

        event_timestamp = getattr(
            event,
            "timestamp",
            None,
        )

        if isinstance(
            event_timestamp,
            datetime,
        ):
            timestamp = event_timestamp

        elif isinstance(
            event_timestamp,
            str,
        ) and event_timestamp:

            timestamp = datetime.fromisoformat(
                event_timestamp.replace(
                    "Z",
                    "+00:00",
                )
            )

        else:
            timestamp = datetime.now(
                timezone.utc
            )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        payload = dict(
            getattr(
                event,
                "payload",
                {},
            )
            or {}
        )

        return cls(
            event_id=str(event_id),
            event_type=event.name,
            timestamp=timestamp,
            payload=payload,
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Return a serialization-friendly representation.
        """

        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
        }
