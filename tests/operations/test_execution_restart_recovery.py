from dataclasses import dataclass

from dairyos.domain.events import Event
from dairyos.operations.execution.models.operational_execution import (
    OperationalExecution,
)
from dairyos.operations.execution.services.execution_tracking_service import (
    ExecutionTrackingService,
)
from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)


@dataclass
class MemoryJournal:
    events: list

    def append(self, event):
        self.events.append(event)

    def all_events(self):
        return list(self.events)

    def latest_execution_sequence(self):
        highest = 0

        for event in self.events:
            if getattr(event, "name", None) != (
                "OPERATIONAL_EXECUTION_CREATED"
            ):
                continue

            execution_id = str(
                (event.payload or {}).get("execution_id", "")
            )

            if execution_id.startswith("EXE-") and execution_id[4:].isdigit():
                highest = max(highest, int(execution_id[4:]))

        return highest


def test_execution_lifecycle_survives_service_restart():
    journal = MemoryJournal(events=[])

    OperationalExecutionService._next_execution_number = None

    first_service = OperationalExecutionService(
        event_journal=journal,
    )

    execution = first_service.create_execution(
        action_id="ACTION-RESTART",
        assigned_to="tester",
    )

    tracking = ExecutionTrackingService(
        event_journal=journal,
    )

    tracking.assign(execution)
    tracking.acknowledge(execution, "tester")
    tracking.start(execution, "tester")
    tracking.complete(
        execution,
        notes="Completed before restart",
        actor="tester",
    )

    assert execution.status == OperationalExecution.COMPLETED

    # Simulate a fresh process: class-level sequence state is gone.
    OperationalExecutionService._next_execution_number = None

    restarted_service = OperationalExecutionService(
        event_journal=journal,
    )

    recovered = restarted_service.get_execution(
        execution.execution_id
    )

    assert recovered is not None
    assert recovered.execution_id == execution.execution_id
    assert recovered.action_id == "ACTION-RESTART"
    assert recovered.assigned_to == "tester"
    assert recovered.status == OperationalExecution.COMPLETED
    assert recovered.completed_by == "tester"
    assert recovered.notes == "Completed before restart"

    next_execution = restarted_service.create_execution(
        action_id="ACTION-NEXT",
        assigned_to="tester",
    )

    assert next_execution.execution_id != execution.execution_id
    assert int(
        next_execution.execution_id.removeprefix("EXE-")
    ) == int(
        execution.execution_id.removeprefix("EXE-")
    ) + 1


def test_execution_lifecycle_events_are_persisted_before_publication():
    journal = MemoryJournal(events=[])
    published = []

    OperationalExecutionService._next_execution_number = None

    service = OperationalExecutionService(
        event_journal=journal,
    )

    execution = service.create_execution(
        action_id="ACTION-PERSIST",
        assigned_to="tester",
    )

    publisher = type(
        "Publisher",
        (),
        {
            "publish": lambda self, event: published.append(event),
        },
    )()

    tracking = ExecutionTrackingService(
        event_publisher=publisher,
        event_journal=journal,
    )

    tracking.start(execution, "tester")

    names = [
        event.name
        for event in journal.events
    ]

    assert "OPERATIONAL_EXECUTION_CREATED" in names
    assert "OPERATIONAL_EXECUTION_STARTED" in names
    assert published
    assert published[-1].event_type == (
        "OPERATIONAL_EXECUTION_STARTED"
    )
