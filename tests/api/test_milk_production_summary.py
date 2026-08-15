from datetime import date, datetime, timedelta, timezone

from dairyos.app import container
from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.operational_finding import OperationalFinding


def _add_milk(
    *,
    animal_id,
    day,
    session,
    morning=None,
    afternoon=None,
    evening=None,
    session_ledger=True,
):
    row = MilkProduction(
        animal_id=animal_id,
        production_date=datetime.combine(
            day,
            datetime.min.time(),
        ),
        milking_session=session,
        morning_yield=morning,
        afternoon_yield=afternoon,
        evening_yield=evening,
        session_ledger=session_ledger,
        status="RECORDED",
    )

    row.calculate_total()

    container.repository_factory.session.add(row)
    container.repository_factory.session.commit()

    return row


def test_milk_production_summary_returns_explicit_no_data(client):
    response = client.get(
        "/farm/milk/production-summary?period=7d"
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["data_status"] == "NO_DATA"
    assert body["kpis"]["total_production_liters"] is None
    assert body["kpis"]["average_per_day_liters"] is None
    assert body["kpis"]["average_per_cow_liters"] is None
    assert body["kpis"]["morning_liters"] is None
    assert body["kpis"]["evening_liters"] is None
    assert body["kpis"]["open_drop_findings"] == 0
    assert body["production_by_animal"]["rows"] == []
    assert body["methodology"]["synthetic_values"] is False


def test_milk_production_summary_aggregates_persisted_data_and_excludes_legacy_rows(
    client,
):
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    eight_days_ago = today - timedelta(days=8)

    _add_milk(
        animal_id="TD-001",
        day=today,
        session="EVENING",
        morning=10.0,
        afternoon=5.0,
        evening=8.0,
    )

    _add_milk(
        animal_id="TD-001",
        day=yesterday,
        session="EVENING",
        morning=9.0,
        afternoon=5.0,
        evening=7.0,
    )

    _add_milk(
        animal_id="TD-002",
        day=today,
        session="EVENING",
        morning=6.0,
        afternoon=4.0,
        evening=5.0,
    )

    _add_milk(
        animal_id="TD-002",
        day=yesterday,
        session="EVENING",
        morning=7.0,
        afternoon=4.0,
        evening=6.0,
    )

    # Deliberately pre-ledger: the Animal ID is valid, but the row is excluded
    # by the production-summary ledger filter.
    _add_milk(
        animal_id="TD-001",
        day=today,
        session="LEGACY_EVENING",
        morning=100.0,
        session_ledger=False,
    )

    # This belongs to the immediately preceding 7-day comparison period.
    _add_milk(
        animal_id="TD-001",
        day=eight_days_ago,
        session="EVENING",
        morning=10.0,
        afternoon=4.0,
        evening=6.0,
    )

    finding_id = (
        "AL-"
        + today.strftime("%y%m%d")
        + "-901"
    )

    finding = OperationalFinding(
        finding_id=finding_id,
        source_module="MILK",
        severity="HIGH",
        title="Test milk drop",
        detail="Test finding",
        status="ACKNOWLEDGED",
        subject_type="ANIMAL",
        subject_id="TD-001",
    )

    container.repository_factory.session.add(finding)
    container.repository_factory.session.commit()

    response = client.get(
        "/farm/milk/production-summary?period=7d"
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["data_status"] == "LIVE_PERSISTED_DATA"
    assert body["period"]["days"] == 7

    # Current 7-day period contains today and yesterday.
    # TD-001 = 23 L today + 21 L yesterday = 44 L
    # TD-002 = 15 L today + 17 L yesterday = 32 L
    # pre-ledger row = excluded
    assert body["kpis"]["total_production_liters"] == 76.0
    assert body["kpis"]["average_per_day_liters"] == 38.0
    assert body["kpis"]["average_per_cow_liters"] == 19.0
    assert body["kpis"]["morning_liters"] == 32.0
    assert body["kpis"]["evening_liters"] == 26.0

    assert body["kpis"]["open_drop_findings"] == 1

    # Previous 7-day comparison period contains the 20 L row.
    assert (
        body["comparison"]["previous_period"][
            "total_production_liters"
        ]
        == 20.0
    )

    # Current 76 L versus previous 20 L = +280%.
    assert (
        body["comparison"]["total_change_percent"]
        == 280.0
    )

    assert len(body["trend"]["current"]) == 2
    assert (
        body["coverage"][
            "animal_days_with_entered_yield"
        ]
        == 4
    )
    assert body["coverage"]["excluded_rows"] == 1

    animal = body["production_by_animal"]

    assert animal["comparison_session"] == "EVENING"

    by_id = {
        row["animal_id"]: row
        for row in animal["rows"]
    }

    assert by_id["TD-001"]["today_liters"] == 8.0
    assert by_id["TD-001"]["previous_liters"] == 7.0
    assert by_id["TD-001"]["status"] == "GOOD"

    assert by_id["TD-002"]["today_liters"] == 5.0
    assert by_id["TD-002"]["previous_liters"] == 6.0
    assert by_id["TD-002"]["status"] == "AMBER"


def test_milk_production_summary_validates_custom_period(client):
    response = client.get(
        "/farm/milk/production-summary"
        "?period=custom"
        "&start_date=2026-08-10"
    )

    assert response.status_code == 400
    assert (
        "requires start_date and end_date"
        in response.json()["detail"]
    )

    response = client.get(
        "/farm/milk/production-summary"
        "?period=custom"
        "&start_date=2026-08-12"
        "&end_date=2026-08-10"
    )

    assert response.status_code == 400
    assert (
        "on or after"
        in response.json()["detail"]
    )

def test_production_summary_uses_same_operational_date_as_next_session(
    monkeypatch,
    client,
):
    from dairyos.api import farm_data_entry

    authoritative_date = date(2026, 8, 10)

    monkeypatch.setattr(
        farm_data_entry,
        "_today",
        lambda: authoritative_date,
    )

    next_session = client.get(
        "/farm/milk/next-session"
    )

    assert next_session.status_code == 200, (
        next_session.text
    )

    next_session_body = next_session.json()

    assert next_session_body[
        "operational_date"
    ] == authoritative_date.isoformat()

    summary = client.get(
        "/farm/milk/production-summary?period=7d"
    )

    assert summary.status_code == 200, (
        summary.text
    )

    summary_body = summary.json()

    assert summary_body[
        "operational_date"
    ] == authoritative_date.isoformat()

    assert summary_body[
        "period"
    ][
        "end_date"
    ] == authoritative_date.isoformat()

    assert summary_body[
        "period"
    ][
        "start_date"
    ] == (
        authoritative_date
        - timedelta(days=6)
    ).isoformat()

