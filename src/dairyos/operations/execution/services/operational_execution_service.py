from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from dairyos.operations.execution.events.execution_events import (
    ExecutionEvents,
)
from dairyos.operations.execution.models.operational_execution import (
    OperationalExecution,
)
from dairyos.runtime.persistent_event_journal import (
    PersistentEventJournal,
)


class OperationalExecutionService:
    """
    Creates, restores, and manages farm operational executions.

    OperationalExecution is the authoritative execution aggregate.

    Persistence contract
    --------------------
    Creation and every lifecycle transition are persisted through the
    operational event journal.

    A fresh service instance therefore reconstructs the aggregate from the
    durable journal instead of starting with an empty in-memory collection.

    Execution identifiers retain the established EXE-#### format and remain
    globally monotonic within the application/database lifecycle.
    """

    _next_execution_number: int | None = None

    _CREATED_EVENT = "OPERATIONAL_EXECUTION_CREATED"
    _ASSIGNED_EVENT = "OPERATIONAL_EXECUTION_ASSIGNED"
    _ACKNOWLEDGED_EVENT = "OPERATIONAL_EXECUTION_ACKNOWLEDGED"
    _STARTED_EVENT = "OPERATIONAL_EXECUTION_STARTED"
    _COMPLETED_EVENT = "OPERATIONAL_EXECUTION_COMPLETED"
    _VERIFIED_EVENT = "OPERATIONAL_EXECUTION_VERIFIED"
    _CLOSED_EVENT = "OPERATIONAL_EXECUTION_CLOSED"

    def __init__(
        self,
        event_journal: PersistentEventJournal | None = None,
    ):
        self.executions: List[OperationalExecution] = []

        self.event_journal = (
            event_journal
            if event_journal is not None
            else PersistentEventJournal()
        )

        self._ensure_execution_sequence()
        self._rehydrate_executions()

    # ------------------------------------------------------------------
    # Durable sequence
    # ------------------------------------------------------------------

    def _ensure_execution_sequence(self) -> None:
        """
        Initialize the process-wide execution sequence from persisted state.
        """

        if OperationalExecutionService._next_execution_number is None:
            highest = self.event_journal.latest_execution_sequence()

            OperationalExecutionService._next_execution_number = (
                highest + 1
            )

    @classmethod
    def _allocate_execution_id(cls) -> str:
        """
        Allocate the next process-wide execution identifier.
        """

        if cls._next_execution_number is None:
            raise RuntimeError(
                "Execution sequence has not been initialized."
            )

        execution_number = cls._next_execution_number
        cls._next_execution_number += 1

        return f"EXE-{execution_number:04d}"

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def create_execution(
        self,
        action_id: str,
        assigned_to: str,
    ) -> OperationalExecution:
        """
        Create and durably persist one operational execution.
        """

        execution = OperationalExecution(
            execution_id=self._allocate_execution_id(),
            action_id=action_id,
            assigned_to=assigned_to,
        )

        self.executions.append(execution)

        self.event_journal.append(
            ExecutionEvents.created(execution)
        )

        return execution

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------

    def _rehydrate_executions(self) -> None:
        """
        Reconstruct execution aggregates from the durable event journal.

        Journal order is authoritative. Unsupported or malformed lifecycle
        events are ignored rather than preventing application startup.
        """

        try:
            events = self.event_journal.all_events()
        except Exception:
            return

        for event in events:
            self._replay_event(event)

    def _replay_event(self, event) -> None:
        event_name = getattr(event, "name", None)
        payload = dict(getattr(event, "payload", None) or {})

        execution_id = payload.get("execution_id")

        if not execution_id:
            return

        execution_id = str(execution_id)

        if event_name == self._CREATED_EVENT:
            if self.get_execution(execution_id) is not None:
                return

            execution = OperationalExecution(
                execution_id=execution_id,
                action_id=str(payload.get("action_id") or ""),
                assigned_to=str(payload.get("assigned_to") or ""),
                status=str(
                    payload.get(
                        "status",
                        OperationalExecution.CREATED,
                    )
                ),
            )

            timestamp = self._event_timestamp(event)

            if timestamp is not None:
                execution.created_at = timestamp

            self.executions.append(execution)
            return

        execution = self.get_execution(execution_id)

        # A lifecycle event without a durable creation event cannot safely
        # reconstruct an aggregate.
        if execution is None:
            return

        timestamp = self._event_timestamp(event)

        if event_name == self._ASSIGNED_EVENT:
            execution.status = OperationalExecution.ASSIGNED
            execution.assigned_to = str(
                payload.get(
                    "assigned_to",
                    execution.assigned_to,
                )
            )
            execution.assigned_at = timestamp
            return

        if event_name == self._ACKNOWLEDGED_EVENT:
            execution.status = OperationalExecution.ACKNOWLEDGED
            execution.acknowledged_by = self._optional_string(
                payload.get("acknowledged_by")
            )
            execution.acknowledged_at = timestamp
            return

        if event_name == self._STARTED_EVENT:
            execution.status = OperationalExecution.STARTED
            execution.started_by = self._optional_string(
                payload.get("started_by")
            )
            execution.started_at = timestamp
            return

        if event_name == self._COMPLETED_EVENT:
            execution.status = OperationalExecution.COMPLETED
            execution.completed_by = self._optional_string(
                payload.get("completed_by")
            )
            execution.notes = self._optional_string(
                payload.get("notes")
            )
            execution.completed_at = timestamp
            return

        if event_name == self._VERIFIED_EVENT:
            execution.status = OperationalExecution.VERIFIED
            execution.verified_by = self._optional_string(
                payload.get("verified_by")
            )
            execution.verified_at = timestamp
            return

        if event_name == self._CLOSED_EVENT:
            execution.status = OperationalExecution.CLOSED
            execution.closed_at = timestamp
            return

    @staticmethod
    def _event_timestamp(event) -> datetime | None:
        value = getattr(event, "timestamp", None)

        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            return value

        try:
            return datetime.fromisoformat(str(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _optional_string(value) -> str | None:
        if value is None:
            return None

        return str(value)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_execution(
        self,
        execution_id: str,
    ) -> Optional[OperationalExecution]:
        """
        Return a recovered or newly-created execution.
        """

        target = str(execution_id)

        for execution in self.executions:
            if execution.execution_id == target:
                return execution

        return None

    def list_executions(
        self,
    ) -> List[OperationalExecution]:
        """
        Return all executions known to this service, including rehydrated
        executions.
        """

        return list(self.executions)
