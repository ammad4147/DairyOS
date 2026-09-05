import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dairyos.data.models.operational_finding import OperationalFinding
from dairyos.data.models.operational_finding_lifecycle_event import (
    OperationalFindingLifecycleEvent,
)
from dairyos.data.repositories.operational_finding_repository import (
    OperationalFindingRepository,
)
from dairyos.farm.findings.services.operational_finding_service import (
    OperationalFindingService,
)


@pytest.fixture()
def service():
    engine = create_engine("sqlite:///:memory:")
    OperationalFinding.__table__.create(engine)
    OperationalFindingLifecycleEvent.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield OperationalFindingService(
            OperationalFindingRepository(session)
        )
    finally:
        session.close()
        engine.dispose()


def test_resolve_reinstate_resolve_keeps_full_history(service):
    finding = service.raise_or_update(
        source_module="MILK",
        severity="HIGH",
        title="Test warning",
        detail="Condition detected",
        dedupe_key="x01-lifecycle-test",
    )
    service.resolve(
        finding.finding_id,
        operator="Operator A",
        resolution_note="Initial corrective action",
    )
    service.reinstate(
        finding.finding_id,
        operator="Administrator",
        reason="Condition still present",
    )

    with pytest.raises(
        ValueError,
        match="resolution note is required",
    ):
        service.resolve(
            finding.finding_id,
            operator="Operator B",
            resolution_note=None,
        )

    service.resolve(
        finding.finding_id,
        operator="Operator B",
        resolution_note="Condition verified corrected",
    )

    events = service.history(finding.finding_id)
    assert [event.event_type for event in events] == [
        "RAISED",
        "RESOLVED",
        "REINSTATED",
        "RESOLVED",
    ]
    assert events[1].note == "Initial corrective action"
    assert events[2].note == "Condition still present"
    assert events[3].note == "Condition verified corrected"
    assert events[2].linked_event_id == events[1].id
    assert events[3].linked_event_id == events[2].id


def test_multiple_reinstatements_remain_traceable(service):
    finding = service.raise_or_update(
        source_module="FINANCE",
        severity="MONITORING",
        title="Repeat warning",
    )

    for operator, resolution, reason in [
        ("One", "First resolution", "First recurrence"),
        ("Two", "Second resolution", "Second recurrence"),
    ]:
        service.resolve(
            finding.finding_id,
            operator=operator,
            resolution_note=resolution,
        )
        service.reinstate(
            finding.finding_id,
            operator="Admin",
            reason=reason,
        )

    service.resolve(
        finding.finding_id,
        operator="Three",
        resolution_note="Final verified resolution",
    )

    events = service.history(finding.finding_id)
    reinstatements = [
        event for event in events
        if event.event_type == "REINSTATED"
    ]
    resolutions = [
        event for event in events
        if event.event_type == "RESOLVED"
    ]

    assert len(reinstatements) == 2
    assert len(resolutions) == 3
    assert resolutions[-1].linked_event_id == reinstatements[-1].id


def test_redetection_appends_observed_event(service):
    finding = service.raise_or_update(
        source_module="MILK",
        severity="HIGH",
        title="Milk reconciliation exception",
        detail="Initial exception",
        dedupe_key="MILK_RECONCILIATION:2026-09-06",
    )

    service.raise_or_update(
        source_module="MILK",
        severity="HIGH",
        title="Milk reconciliation exception",
        detail="Observed again",
        dedupe_key="MILK_RECONCILIATION:2026-09-06",
    )

    events = service.history(finding.finding_id)
    assert [event.event_type for event in events] == ["RAISED", "OBSERVED"]
    assert events[1].note == "Observed again"
