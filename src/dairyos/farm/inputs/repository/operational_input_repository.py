import json
import os
import tempfile
import time
from dairyos.platform.paths import resolve_storage_file
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from dairyos.domain.events.operational_input_received import (
    OperationalInputReceived,
)


class OperationalInputRepository:
    """
    Durable persistence boundary for operational inputs.

    Operational inputs are part of the farm's audit trail and therefore
    must survive application restarts. The repository keeps the domain
    event contract independent from the storage format while using a
    small JSON-backed materialized repository for this subsystem.
    """

    def __init__(self, storage_path=None):
        self.storage_path = (
            Path(storage_path)
            if storage_path
            else resolve_storage_file("operational_inputs.json")
        )
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
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

    @staticmethod
    def _serialize(value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, dict):
            return {key: OperationalInputRepository._serialize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [OperationalInputRepository._serialize(item) for item in value]
        return value

    def _persist(self):
        payload = []

        for record in self._records:
            payload.append(
                {
                    "input_type": record.input_type,
                    "payload": self._serialize(dict(record.payload or {})),
                    "source": record.source,
                    "actor": record.actor,
                    "event_id": record.event_id,
                    "timestamp": self._serialize(record.timestamp),
                }
            )

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Use a unique temporary file per write. A shared .tmp pathname is
        # unsafe when more than one repository instance persists concurrently,
        # especially on Windows where an open temp file can block replacement.
        fd, temporary_name = tempfile.mkstemp(
            prefix=f"{self.storage_path.name}.",
            suffix=".tmp",
            dir=self.storage_path.parent,
            text=True,
        )
        temporary_path = Path(temporary_name)

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(
                    payload,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )
                file.flush()
                os.fsync(file.fileno())

            # The temp file handle is fully closed before replacement. Windows
            # otherwise may return WinError 5 even though the write succeeded.
            last_error = None
            for attempt in range(3):
                try:
                    temporary_path.replace(self.storage_path)
                    last_error = None
                    break
                except PermissionError as exc:
                    last_error = exc
                    if attempt == 2:
                        raise
                    time.sleep(0.05 * (attempt + 1))

            if last_error is not None:
                raise last_error
        finally:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass

    def _load(self):
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            # The event journal remains the authoritative event-history
            # boundary, so an unavailable materialized repository must not
            # prevent application startup.
            self._records = []
            return

        for item in data:
            timestamp = item.get("timestamp")
            if isinstance(timestamp, str) and timestamp:
                timestamp = datetime.fromisoformat(timestamp)
            if timestamp is None:
                from datetime import timezone
                timestamp = datetime.now(timezone.utc)

            self._records.append(
                OperationalInputReceived(
                    input_type=item["input_type"],
                    payload=dict(item.get("payload") or {}),
                    source=item.get("source", ""),
                    actor=item.get("actor", ""),
                    event_id=item.get("event_id") or str(uuid4()),
                    timestamp=timestamp,
                )
            )
