import json


from tests.lifecycle.test_milk_operational_lifecycle import (
    _ledger,
    _milk,
    _production_summary,
    _reconciliation,
    _register,
)


def _find_key_values(value, wanted_key):
    found = []

    if isinstance(value, dict):
        for key, item in value.items():
            if key == wanted_key:
                found.append(item)
            found.extend(_find_key_values(item, wanted_key))

    elif isinstance(value, list):
        for item in value:
            found.extend(_find_key_values(item, wanted_key))

    return found


def _find_numeric(value, target, tolerance=0.001):
    if isinstance(value, (int, float)):
        return abs(float(value) - float(target)) <= tolerance

    if isinstance(value, dict):
        return any(
            _find_numeric(item, target, tolerance)
            for item in value.values()
        )

    if isinstance(value, list):
        return any(
            _find_numeric(item, target, tolerance)
            for item in value
        )

    return False


def test_complete_milk_surface_certification(client):
    day = _register(client, "MILK-SURFACE-A")
    animal_b = _register(client, "MILK-SURFACE-B")

    animal_a = day
    operational_date = __import__("datetime").date.today()

    # ==============================================================
    # AUTHORITATIVE PRODUCTION INPUT
    #
    # Animal A: 30 + 25 = 55 L
    # Animal B: 35 + 25 = 60 L
    # Farm total: 115 L
    # ==============================================================

    _milk(client, animal_a, operational_date, "MORNING", 30.0)
    _milk(client, animal_a, operational_date, "EVENING", 25.0)

    _milk(client, animal_b, operational_date, "MORNING", 35.0)
    _milk(client, animal_b, operational_date, "EVENING", 25.0)

    # ==============================================================
    # AUTHORITATIVE DESTINATIONS
    #
    # SOLD       = 100 L
    # DOMESTIC   =   5 L
    # CALF_FEED  =   5 L
    # WASTAGE    =   5 L
    #
    # Total accounted = 115 L
    # Unaccounted     =   0 L
    # ==============================================================

    sold = client.post(
        "/farm/milk/dispositions",
        json={
            "production_date": operational_date.isoformat(),
            "disposition_type": "SOLD",
            "quantity_litres": 100.0,
            "sale_id": "MILK-SURFACE-SALE-001",
            "counterparty": "SURFACE-CERTIFICATION-CUSTOMER",
            "selling_price_per_litre": 225.0,
            "notes": "Milk surface certification",
        },
    )
    assert sold.status_code == 200, sold.text
    sold_payload = sold.json()
    print()
    print("=== SOLD POST RESPONSE ===")
    print(json.dumps(sold_payload, indent=2, default=str))
    print("==========================")

    domestic = client.post(
        "/farm/milk/dispositions",
        json={
            "production_date": operational_date.isoformat(),
            "disposition_type": "DOMESTIC_USE",
            "quantity_litres": 5.0,
            "notes": "Milk surface certification",
        },
    )
    assert domestic.status_code == 200, domestic.text

    calves = client.post(
        "/farm/milk/dispositions",
        json={
            "production_date": operational_date.isoformat(),
            "disposition_type": "CALF_FEED",
            "quantity_litres": 5.0,
            "notes": "Milk surface certification",
        },
    )
    assert calves.status_code == 200, calves.text

    wastage = client.post(
        "/farm/milk/dispositions",
        json={
            "production_date": operational_date.isoformat(),
            "disposition_type": "WASTAGE",
            "quantity_litres": 5.0,
            "notes": "Milk surface certification",
        },
    )
    assert wastage.status_code == 200, wastage.text

    # ==============================================================
    # INDEPENDENT RECONSTRUCTION FROM /farm/milk/ledger
    # ==============================================================

    ledger = _ledger(
        client,
        operational_date,
    )

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

    independent_production = round(
        sum(
            float(row.get("total_yield") or 0.0)
            for row in production_rows
        ),
        3,
    )

    independent_sold = round(
        sum(
            float(row.get("quantity_litres") or 0.0)
            for row in disposition_rows
            if row.get("disposition_type") == "SOLD"
        ),
        3,
    )

    independent_non_sale = round(
        sum(
            float(row.get("quantity_litres") or 0.0)
            for row in disposition_rows
            if row.get("disposition_type")
            in {
                "DOMESTIC_USE",
                "CALF_FEED",
                "WASTAGE",
            }
        ),
        3,
    )

    independent_unaccounted = round(
        independent_production
        - independent_sold
        - independent_non_sale,
        3,
    )

    assert independent_production == 115.0
    assert independent_sold == 100.0
    assert independent_non_sale == 15.0
    assert independent_unaccounted == 0.0

    # ==============================================================
    # SURFACE 1 — RECONCILIATION
    # ==============================================================

    reconciliation = _reconciliation(
        client,
        operational_date,
    )

    assert reconciliation["production_complete"] is True
    assert float(reconciliation["produced_litres"]) == 115.0
    assert float(reconciliation["sold_litres"]) == 100.0
    assert float(reconciliation["non_sale_accounted_litres"]) == 15.0
    assert float(reconciliation["unaccounted_litres"]) == 0.0
    assert reconciliation["status"] == "RECONCILED"

    # ==============================================================
    # SURFACE 2 — PRODUCTION SUMMARY
    # ==============================================================

    summary = _production_summary(
        client,
        operational_date,
        operational_date,
    )

    kpis = summary["kpis"]

    assert float(
        kpis["total_production_liters"]
    ) == 115.0

    assert float(
        kpis["morning_liters"]
    ) == 65.0

    assert float(
        kpis["evening_liters"]
    ) == 50.0

    # ==============================================================
    # SURFACE 3 — DASHBOARD
    # ==============================================================

    dashboard_response = client.get("/dashboard")
    assert dashboard_response.status_code == 200, dashboard_response.text

    dashboard = dashboard_response.json()

    milk_payload = dashboard.get("milk", {})

    assert milk_payload, (
        "Dashboard does not expose a milk payload."
    )

    dashboard_total = None

    for key in (
        "total_production_liters",
        "current_month_production",
    ):
        if milk_payload.get(key) is not None:
            dashboard_total = float(
                milk_payload[key]
            )
            break

    assert dashboard_total is not None, (
        "Dashboard exposes neither total_production_liters "
        "nor current_month_production."
    )

    assert dashboard_total >= 115.0

    # ==============================================================
    # SURFACE 4 — ANIMAL TRACEABILITY
    # ==============================================================

    trace_a = client.get(
        f"/farm/milk/{animal_a}/traceability"
    )
    assert trace_a.status_code == 200, trace_a.text

    trace_a_payload = trace_a.json()

    assert trace_a_payload["data_status"] == "LIVE_PERSISTED"
    assert trace_a_payload["animal"]["animal_id"] == animal_a
    assert trace_a_payload["record_count"] == 1
    assert float(trace_a_payload["total_litres"]) == 55.0

    trace_b = client.get(
        f"/farm/milk/{animal_b}/traceability"
    )
    assert trace_b.status_code == 200, trace_b.text

    trace_b_payload = trace_b.json()

    assert trace_b_payload["data_status"] == "LIVE_PERSISTED"
    assert trace_b_payload["animal"]["animal_id"] == animal_b
    assert trace_b_payload["record_count"] == 1
    assert float(trace_b_payload["total_litres"]) == 60.0

    # ==============================================================
    # SURFACE 5 — ANIMAL PASSPORT
    # ==============================================================

    passport_a_response = client.get(
        f"/farm/animals/{animal_a}/passport"
    )
    assert passport_a_response.status_code == 200, (
        passport_a_response.text
    )

    passport_a = passport_a_response.json()

    assert _find_numeric(
        passport_a,
        55.0,
    ), (
        "Animal Passport does not expose the persisted 55 L "
        "milk history for Animal A."
    )

    # Explicitly inspect likely lifetime-total fields if present.
    passport_lifetime = _find_key_values(
        passport_a,
        "lifetime_milk_liters",
    )

    if passport_lifetime:
        assert any(
            abs(float(value) - 55.0) <= 0.001
            for value in passport_lifetime
        )

    # ==============================================================
    # ==============================================================
    # SURFACE 6 — SALE CONTRACT
    #
    # Validate the authoritative persisted representation rather than
    # assuming the POST response shape is the complete traceability record.
    # ==============================================================

    sold_rows = [
        row
        for row in disposition_rows
        if row.get("disposition_type") == "SOLD"
        and row.get("sale_id") == "MILK-SURFACE-SALE-001"
    ]

    assert len(sold_rows) == 1, (
        "Exactly one persisted SOLD disposition was expected."
    )

    sold_row = sold_rows[0]

    assert sold_row["disposition_type"] == "SOLD"
    assert float(
        sold_row["quantity_litres"]
    ) == 100.0
    assert sold_row["sale_id"] == (
        "MILK-SURFACE-SALE-001"
    )
    assert float(
        sold_row["selling_price_per_litre"]
    ) == 225.0
    assert float(
        sold_row["amount_due"]
    ) == 22500.0
    assert sold_row["status"] == "RECORDED"
    # SURFACE 7 — RELOAD / PERSISTENCE
    # ==============================================================

    reloaded_ledger = _ledger(
        client,
        operational_date,
    )

    reloaded_production = round(
        sum(
            float(row.get("total_yield") or 0.0)
            for row in reloaded_ledger["production"]
            if row.get("status") != "VOID"
        ),
        3,
    )

    reloaded_dispositions = round(
        sum(
            float(row.get("quantity_litres") or 0.0)
            for row in reloaded_ledger["dispositions"]
            if row.get("status") != "VOID"
        ),
        3,
    )

    assert reloaded_production == 115.0
    assert reloaded_dispositions == 115.0

    # ==============================================================
    # FINAL RECONCILIATION
    # ==============================================================

    final_reconciliation = _reconciliation(
        client,
        operational_date,
    )

    assert final_reconciliation["status"] == "RECONCILED"
    assert float(
        final_reconciliation["produced_litres"]
    ) == 115.0
    assert float(
        final_reconciliation["accounted_litres"]
    ) == 115.0
    assert float(
        final_reconciliation["unaccounted_litres"]
    ) == 0.0

    print()
    print("=" * 78)
    print("DAIRYOS MILK SURFACE CERTIFICATION")
    print("=" * 78)
    print("Independent production:", independent_production)
    print("Independent sold:", independent_sold)
    print("Independent non-sale:", independent_non_sale)
    print("Independent unaccounted:", independent_unaccounted)
    print("Reconciliation:", reconciliation["status"])
    print("Production summary:", kpis["total_production_liters"])
    print("Dashboard total:", dashboard_total)
    print("Animal A traceability:", trace_a_payload["total_litres"])
    print("Animal B traceability:", trace_b_payload["total_litres"])
    print("Reloaded production:", reloaded_production)
    print("Reloaded dispositions:", reloaded_dispositions)
    print("=" * 78)
    print("COMPLETE MILK SURFACE CERTIFICATION: PASS")
    print("=" * 78)



