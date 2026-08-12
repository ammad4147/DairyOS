import json
from datetime import datetime
from pathlib import Path

from dairyos.domain.events.operational_input_received import (
    OperationalInputReceived,
)


class OperationalInputRepository:
    """
    Durable persistence boundary for operational inputs.

    Operational inputs are part of the farm's audit trail and therefore
    must survive application restarts.  The repository deliberately keeps
    the domain-event contract independent from the storage format while
    using a small append-only JSON store for this subsystem.
    """

    def __init__(
        self,
        storage_path=None,
    ):
        self.storage_path = (
            Path(storage_path)
            if storage_path
            else Path("data/storage/operational_inputs.json")
        )
        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._records = []
        self._load()

    def save(self, record):
        """Persist one operational input, idempotently by event identity."""
        event_id = getattr(record, "event_id", None)

        if event_id is not None:
            for existing in self._records:
                if getattr(existing, "event_id", None) == event_id:
                    return existing

        self._records.append(record)
        self._persist()
        return record

    def list_all(self):
        return list(self._records)

    def find_by_type(self, input_type):
        return [
            record
            for record in self._records
            if record.input_type == input_type
        ]

    def clear(self):
        """Clear persisted operational inputs; intended for controlled tests."""
        self._records = []
        self._persist()

    def _persist(self):
        payload = []

        for record in self._records:
            timestamp = getattr(record, "timestamp", None)
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()

            payload.append(
                {
                    "input_type": record.input_type,
                    "payload": dict(record.payload or {}),
                    "source": record.source,
                    "actor": record.actor,
                    "event_id": record.event_id,
                    "timestamp": timestamp,
                }
            )

        temporary_path = self.storage_path.with_suffix(
            self.storage_path.suffix + ".tmp"
        )

        with open(
            temporary_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                payload,
                file,
                indent=2,
                ensure_ascii=False,
            )

        temporary_path.replace(self.storage_path)

    def _load(self):
        if not self.storage_path.exists():
            return

        try:
            with open(
                self.storage_path,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            # A missing/corrupt optional projection must not prevent the
            # application from starting; the event journal remains the
            # authoritative event-history boundary.
            self._records = []
            return

        for item in data:
            timestamp = item.get("timestamp")
            if isinstance(timestamp, str) and timestamp:
                timestamp = datetime.fromisoformat(timestamp)

            self._records.append(
                OperationalInputReceived(
                    input_type=item["input_type"],
                    payload=dict(item.get("payload") or {}),
                    source=item.get("source", ""),
                    actor=item.get("actor", ""),
                    event_id=item.get("event_id")
                    or OperationalInputReceived(
                        input_type=item["input_type"],
                        payload=dict(item.get("payload") or {}),
                        source=item.get("source", ""),
                        actor=item.get("actor", ""),
                    ).event_id,
                    timestamp=timestamp
                    or OperationalInputReceived(
                        input_type=item["input_type"],
                        payload=dict(item.get("payload") or {}),
                        source=item.get("source", ""),
                        actor=item.get("actor", ""),
                    ).timestamp,
                )
            )
