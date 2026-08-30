from datetime import date

from tests.lifecycle.test_milk_operational_lifecycle import (
    _ledger,
    _milk,
    _operational_date,
    _production_summary,
    _reconciliation,
    _register,
)


def test_incomplete_milk_surface_certification(client):
    day = _operational_date()

    animal = _register(
        client,
        "MILK-INCOMPLETE-SURFACE",
    )

    # This animal is governed for TWICE_DAILY production.
    # Only MORNING is entered.
    #
    # Known production = 30 L
    # Missing expected session = EVENING
    # Therefore production remains operationally incomplete.
    response = _milk(
        client,
        animal,
        day,
        "MORNING",
        30.0,
    )

    assert response is not None

    # --------------------------------------------------------------
    # SURFACE 1 — RAW PERSISTED LEDGER
    # --------------------------------------------------------------

    ledger = _ledger(
        client,
        day,
    )

    production_rows = [
        row
        for row in ledger["production"]
        if row.get("status") != "VOID"
    ]

    assert production_rows

    known_litres = round(
        sum(
            float(row.get("total_yield") or 0.0)
            for row in production_rows
        ),
        3,
    )

    assert known_litres == 30.0

    # --------------------------------------------------------------
    # SURFACE 2 — RECONCILIATION
    #
    # Incomplete is NOT the same thing as zero.
    # --------------------------------------------------------------

    reconciliation = _reconciliation(
        client,
        day,
    )

    print()
    print("=" * 78)
    print("INCOMPLETE MILK SURFACE CERTIFICATION")
    print("=" * 78)
    print("Reconciliation:", reconciliation)

    assert reconciliation["production_complete"] is False
    assert reconciliation["status"] == "PRODUCTION_INCOMPLETE"

    # Incomplete means the day is not closed, not that known production
    # disappears. Persisted production remains visible.
    assert float(
        reconciliation["produced_litres"] or 0.0
    ) == 30.0

    assert known_litres == 30.0

    # --------------------------------------------------------------
    # SURFACE 3 — PRODUCTION SUMMARY
    #
    # Summary must expose known persisted production even though the
    # operational day is incomplete.
    # --------------------------------------------------------------

    summary = _production_summary(
        client,
        day,
        day,
    )

    summary_total = float(
        summary["kpis"]["total_production_liters"] or 0.0
    )

    print("Production summary:", summary_total)

    assert summary_total == 30.0

    # --------------------------------------------------------------
    # SURFACE 4 — DASHBOARD
    #
    # Dashboard must not turn a known 30 L into zero merely because
    # another expected session remains outstanding.
    # --------------------------------------------------------------

    dashboard_response = client.get(
        "/dashboard"
    )

    assert dashboard_response.status_code == 200, (
        dashboard_response.text
    )

    dashboard = dashboard_response.json()
    milk = dashboard.get("milk", {})

    assert milk, "Dashboard does not expose a milk payload."

    dashboard_total = None

    for key in (
        "current_month_production",
        "total_production_liters",
    ):
        value = milk.get(key)

        if value is not None:
            dashboard_total = float(value)
            break

    assert dashboard_total is not None, (
        "Dashboard exposes neither current_month_production "
        "nor total_production_liters."
    )

    print("Dashboard known production:", dashboard_total)

    assert dashboard_total >= 30.0

    # --------------------------------------------------------------
    # SURFACE 5 — ANIMAL TRACEABILITY
    # --------------------------------------------------------------

    trace_response = client.get(
        f"/farm/milk/{animal}/traceability"
    )

    assert trace_response.status_code == 200, (
        trace_response.text
    )

    trace = trace_response.json()

    assert trace["data_status"] == "LIVE_PERSISTED"
    assert trace["animal"]["animal_id"] == animal
    assert float(trace["total_litres"]) == 30.0

    # --------------------------------------------------------------
    # SURFACE 6 — ANIMAL PASSPORT
    # --------------------------------------------------------------

    passport_response = client.get(
        f"/farm/animals/{animal}/passport"
    )

    assert passport_response.status_code == 200, (
        passport_response.text
    )

    passport = passport_response.json()

    # The passport is a projection and may expose this under a
    # lifetime-milk field rather than a top-level field. Search the
    # returned JSON without assuming a particular presentation shape.
    def contains_numeric(value, target):
        if isinstance(value, (int, float)):
            return abs(float(value) - target) <= 0.001

        if isinstance(value, dict):
            return any(
                contains_numeric(item, target)
                for item in value.values()
            )

        if isinstance(value, list):
            return any(
                contains_numeric(item, target)
                for item in value
            )

        return False

    assert contains_numeric(
        passport,
        30.0,
    ), (
        "Animal Passport does not expose the known persisted "
        "30 L milk production."
    )

    # --------------------------------------------------------------
    # SURFACE 7 — RELOAD / PERSISTENCE
    #
    # Reloading all surfaces must preserve the distinction:
    #
    # known production = 30 L
    # operational completeness = FALSE
    # --------------------------------------------------------------

    reloaded_ledger = _ledger(
        client,
        day,
    )

    reloaded_production = round(
        sum(
            float(row.get("total_yield") or 0.0)
            for row in reloaded_ledger["production"]
            if row.get("status") != "VOID"
        ),
        3,
    )

    assert reloaded_production == 30.0

    reloaded_reconciliation = _reconciliation(
        client,
        day,
    )

    assert (
        reloaded_reconciliation["production_complete"]
        is False
    )

    assert (
        reloaded_reconciliation["status"]
        == "PRODUCTION_INCOMPLETE"
    )

    print("Reloaded known production:", reloaded_production)
    print(
        "Reloaded reconciliation:",
        reloaded_reconciliation["status"],
    )

    print("=" * 78)
    print(
        "INCOMPLETE MILK SURFACE CERTIFICATION: PASS"
    )
    print("=" * 78)

