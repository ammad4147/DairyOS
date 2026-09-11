"""Pagination checks for bounded, read-only operational evidence."""

from datetime import UTC, date, datetime
from uuid import uuid4

from dairyos.api.dependencies import get_container
from dairyos.assistant.operational import read_operational_data, read_operational_logs
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.models.milk_production import MilkProduction


def test_operational_records_and_logs_expose_stable_pages(client, registered_animal, monkeypatch):
    from dairyos.farm.settings.services.operational_date_authority import (
        OperationalDateAuthority,
    )

    monkeypatch.setattr(
        OperationalDateAuthority,
        "current_date",
        lambda self: date(2026, 9, 10),
    )
    session = get_container().repository_factory.session
    for day, litres in ((date(2026, 9, 1), 10.0), (date(2026, 9, 2), 20.0)):
        session.add(
            MilkProduction(
                animal_id=registered_animal,
                production_date=datetime.combine(day, datetime.min.time()),
                recorded_at=datetime.combine(day, datetime.min.time()),
                total_yield=litres,
                status="RECORDED",
            )
        )
    for index in range(2):
        session.add(
            EventJournalModel(
                event_id=f"PAGINATION-{uuid4().hex}",
                event_type="PaginationProbe",
                timestamp=datetime(2026, 9, 1 + index, tzinfo=UTC).replace(tzinfo=None),
                payload={"probe": index},
            )
        )
    session.commit()

    first = read_operational_data(
        question="What was milk production in September 2026?",
        page=1,
        page_size=1,
    )
    second = read_operational_data(
        question="What was milk production in September 2026?",
        page=2,
        page_size=1,
    )
    first_page = first["evidence"]["pagination"]["daily"]
    second_page = second["evidence"]["pagination"]["daily"]
    assert first_page["page"] == 1
    assert first_page["returned_records"] == 1
    assert first_page["has_next"] is True
    assert second_page["page"] == 2
    assert second["evidence"]["daily"][0]["date"] != first["evidence"]["daily"][0]["date"]

    logs = read_operational_logs(
        question="show event history and logs",
        page=2,
        page_size=1,
    )
    journal_page = logs["pagination"]["event_journal"]
    assert journal_page["page"] == 2
    assert journal_page["returned_records"] == 1
    assert logs["read_only"] is True
