"""
DairyOS Milk operational lifecycle certification.

The test intentionally derives all expected values independently from the
entries submitted through the public APIs, then reconciles those values against
the persisted ledger, reconciliation endpoint, production summary, and
Dashboard projection.
"""

from __future__ import annotations

from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


def _operational_date():
    return OperationalDateAuthority().current_date()


def _register(client, ear_tag):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "ear_tag": ear_tag,
            "breed": "HF",
            "sex": "FEMALE",
            "lifecycle_status": "LACTATING",
            "is_currently_milking": True,
            "milking_frequency": "TWICE_DAILY",
        },
    )

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["system_generated_animal_id"] is True
    assert payload["animal_id"]

    return payload["animal_id"]


def _milk(client, animal_id, day, session, litres):
    field = f"{session.lower()}_yield"

    response = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            field: float(litres),
            "milking_session": session,
            "production_date": day.isoformat(),
            "operator": "MILK-LIFECYCLE-CERTIFICATION",
        },
    )

    assert response.status_code == 200, response.text

    return response.json()


def _disposition(client, day, disposition_type, litres):
    disposition = str(disposition_type).upper()

    payload = {
        "production_date": day.isoformat(),
        "disposition_type": disposition,
        "quantity_litres": float(litres),
        "sale_id": None,
        "counterparty": None,
        "selling_price_per_litre": None,
        "notes": "Milk lifecycle certification",
    }

    if disposition == "SOLD":
        payload["sale_id"] = "MILK-LIFECYCLE-SALE-001"
        payload["counterparty"] = "Lifecycle Test Customer"
        payload["selling_price_per_litre"] = 200.0

    response = client.post(
        "/farm/milk/dispositions",
        json=payload,
    )

    assert response.status_code == 200, response.text

    return response.json()

def _ledger(client, day):
    response = client.get(
        "/farm/milk/ledger",
        params={
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
        },
    )

    assert response.status_code == 200, response.text

    return response.json()


def _reconciliation(client, day):
    response = client.get(
        "/farm/milk/reconciliation",
        params={
            "production_date": day.isoformat(),
        },
    )

    assert response.status_code == 200, response.text

    return response.json()


def _production_summary(client, start, end):
    response = client.get(
        "/farm/milk/production-summary",
        params={
            "period": "custom",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
    )

    assert response.status_code == 200, response.text

    return response.json()


def _dashboard(client):
    response = client.get("/dashboard")

    assert response.status_code == 200, response.text

    return response.json()


def _production_total(rows):
    return round(
        sum(
            float(row.get("total_yield") or 0.0)
            for row in rows
            if row.get("status") != "VOID"
        ),
        3,
    )


def _disposition_total(rows, disposition_type=None):
    return round(
        sum(
            float(row.get("quantity_litres") or 0.0)
            for row in rows
            if row.get("status") != "VOID"
            and (
                disposition_type is None
                or row.get("disposition_type") == disposition_type
            )
        ),
        3,
    )


def test_complete_milk_lifecycle_reconciles_every_surface(client):
    day = _operational_date()

    animal_a = _register(client, "MILK-LIFECYCLE-A")
    animal_b = _register(client, "MILK-LIFECYCLE-B")

    # --------------------------------------------------------------
    # Stage 1: production
    #
    # A / MORNING = 30 L
    # B / EVENING = 45 L
    #
    # Expected production = 75 L
    # --------------------------------------------------------------
    _milk(client, animal_a, day, "MORNING", 30.0)
    _milk(client, animal_b, day, "EVENING", 45.0)

    # --------------------------------------------------------------
    # Stage 2: non-sale dispositions
    #
    # Domestic use = 2 L
    # Calf feed    = 5 L
    #
    # NO zero-valued WASTAGE record is created because the API correctly
    # requires quantity_litres > 0. Absence of a wastage record means
    # wastage is zero.
    # --------------------------------------------------------------
    _disposition(
        client,
        day,
        "DOMESTIC_USE",
        2.0,
    )

    _disposition(
        client,
        day,
        "CALF_FEED",
        5.0,
    )

    ledger = _ledger(client, day)

    production_rows = [
        row
        for row in ledger["production"]
        if row.get("status") != "VOID"
    ]

    disposition_rows = [
        row
        for row in ledger["dispositions"]
        if row.get("status") != "VOID"
    ]

    production = _production_total(production_rows)
    sold = _disposition_total(
        disposition_rows,
        "SOLD",
    )
    domestic = _disposition_total(
        disposition_rows,
        "DOMESTIC_USE",
    )
    calves = _disposition_total(
        disposition_rows,
        "CALF_FEED",
    )
    wastage = _disposition_total(
        disposition_rows,
        "WASTAGE",
    )

    expected_unaccounted = round(
        production
        - sold
        - domestic
        - calves
        - wastage,
        3,
    )

    print()
    print("=" * 78)
    print("MILK LIFECYCLE — AUTHORITATIVE INPUT RECONCILIATION")
    print("=" * 78)
    print("Production:", production)
    print("Sold:", sold)
    print("Domestic:", domestic)
    print("Calf feed:", calves)
    print("Wastage:", wastage)
    print(
        "Independent unaccounted:",
        expected_unaccounted,
    )

    assert production == 75.0
    assert sold == 0.0
    assert domestic == 2.0
    assert calves == 5.0
    assert wastage == 0.0
    assert expected_unaccounted == 68.0

    print("Input arithmetic: PASS")

    # --------------------------------------------------------------
    # Stage 3: reconciliation endpoint
    # --------------------------------------------------------------
    reconciliation = _reconciliation(
        client,
        day,
    )

    print()
    print("RECONCILIATION ENDPOINT")
    print(reconciliation)

    assert (
        float(
            reconciliation["produced_litres"] or 0.0
        )
        == 75.0
    )

    assert (
        float(
            reconciliation["sold_litres"] or 0.0
        )
        == 0.0
    )

    assert (
        float(
            reconciliation[
                "non_sale_accounted_litres"
            ]
            or 0.0
        )
        == 7.0
    )

    assert (
        float(
            reconciliation["unaccounted_litres"]
            or 0.0
        )
        == 68.0
    )

    print("Daily reconciliation: PASS")

    # --------------------------------------------------------------
    # Stage 4: production summary
    # --------------------------------------------------------------
    summary = _production_summary(
        client,
        day,
        day,
    )

    total_summary = float(
        summary["kpis"]["total_production_liters"]
        or 0.0
    )

    print()
    print("PRODUCTION SUMMARY")
    print("Total production:", total_summary)

    assert total_summary == 75.0

    print("Production summary: PASS")

    # --------------------------------------------------------------
    # Stage 5: Dashboard
    # --------------------------------------------------------------
    dashboard = _dashboard(client)
    dashboard_milk = dashboard.get("milk", {})

    print()
    print("DASHBOARD MILK PROJECTION")
    print(dashboard_milk)

    dashboard_production = (
        dashboard_milk.get(
            "total_production_liters"
        )
    )

    if dashboard_production is None:
        dashboard_production = dashboard_milk.get(
            "current_month_production"
        )

    if dashboard_production is not None:
        assert float(dashboard_production) == 75.0
        print("Dashboard production: PASS")
    else:
        raise AssertionError(
            "Dashboard exposes neither total_production_liters "
            "nor current_month_production."
        )

    # --------------------------------------------------------------
    # Stage 6: add a 20 L sale
    #
    # Expected:
    #   production   75
    #   sold         20
    #   domestic      2
    #   calf feed     5
    #   wastage       0
    #   unaccounted  48
    # --------------------------------------------------------------
    _disposition(
        client,
        day,
        "SOLD",
        20.0,
    )

    after_sale = _reconciliation(
        client,
        day,
    )

    print()
    print("AFTER 20 L SALE")
    print(after_sale)

    assert (
        float(
            after_sale["produced_litres"] or 0.0
        )
        == 75.0
    )

    assert (
        float(
            after_sale["sold_litres"] or 0.0
        )
        == 20.0
    )

    assert (
        float(
            after_sale[
                "non_sale_accounted_litres"
            ]
            or 0.0
        )
        == 7.0
    )

    assert (
        float(
            after_sale["unaccounted_litres"]
            or 0.0
        )
        == 48.0
    )

    print("Post-sale reconciliation: PASS")

    # --------------------------------------------------------------
    # Stage 7: reload / persisted read-back
    # --------------------------------------------------------------
    reloaded_ledger = _ledger(
        client,
        day,
    )

    reloaded_production = _production_total(
        reloaded_ledger["production"]
    )

    reloaded_sold = _disposition_total(
        reloaded_ledger["dispositions"],
        "SOLD",
    )

    reloaded_domestic = _disposition_total(
        reloaded_ledger["dispositions"],
        "DOMESTIC_USE",
    )

    reloaded_calves = _disposition_total(
        reloaded_ledger["dispositions"],
        "CALF_FEED",
    )

    reloaded_wastage = _disposition_total(
        reloaded_ledger["dispositions"],
        "WASTAGE",
    )

    reloaded_unaccounted = round(
        reloaded_production
        - reloaded_sold
        - reloaded_domestic
        - reloaded_calves
        - reloaded_wastage,
        3,
    )

    print()
    print("RELOADED PERSISTED LEDGER")
    print("Production:", reloaded_production)
    print("Sold:", reloaded_sold)
    print("Domestic:", reloaded_domestic)
    print("Calf feed:", reloaded_calves)
    print("Wastage:", reloaded_wastage)
    print(
        "Recalculated unaccounted:",
        reloaded_unaccounted,
    )

    assert reloaded_production == 75.0
    assert reloaded_sold == 20.0
    assert reloaded_domestic == 2.0
    assert reloaded_calves == 5.0
    assert reloaded_wastage == 0.0
    assert reloaded_unaccounted == 48.0

    print("Persisted read-back: PASS")

    # --------------------------------------------------------------
    # Stage 8: final Dashboard read
    # --------------------------------------------------------------
    final_dashboard = _dashboard(client)

    print()
    print("FINAL DASHBOARD MILK PROJECTION")
    print(final_dashboard.get("milk"))

    print()
    print("=" * 78)
    print("MILK LIFECYCLE CERTIFICATION")
    print("=" * 78)
    print("Production persistence: PASS")
    print("Disposition persistence: PASS")
    print("Reconciliation: PASS")
    print("Production summary: PASS")
    print("Dashboard production: PASS")
    print("Sale transition: PASS")
    print("Reload persistence: PASS")
    print("=" * 78)

