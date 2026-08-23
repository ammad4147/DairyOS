import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from dairyos.app import app
from tests.conftest import _reset_test_persistence


DAY_1 = date(2026, 8, 24)
DAY_2 = DAY_1 - timedelta(days=1)


def check(response, *expected):
    if response.status_code not in expected:
        raise AssertionError(
            f"{response.request.method} {response.request.url} "
            f"-> {response.status_code}: {response.text}"
        )
    return response


def get_json(client, path):
    return check(client.get(path), 200).json()


def post_json(client, path, payload, expected=(200, 201)):
    return check(client.post(path, json=payload), *expected).json()


def create_animal(client, frequency="THRICE_DAILY", tag="EDGE"):
    return post_json(
        client,
        "/farm/animals",
        {
            "animal_type": "COW",
            "breed": "SIM-HF",
            "lifecycle_status": "LACTATING",
            "is_currently_milking": True,
            "milking_frequency": frequency,
            "ear_tag": tag,
        },
    )["animal_id"]


def record_milk(client, animal_id, session, litres, production_date):
    return post_json(
        client,
        "/farm/milk",
        {
            "animal_id": animal_id,
            "production_date": production_date.isoformat(),
            "milking_session": session,
            "morning_yield": litres if session == "MORNING" else None,
            "afternoon_yield": litres if session == "AFTERNOON" else None,
            "evening_yield": litres if session == "EVENING" else None,
            "operator": "EDGE-SIM",
        },
    )


def finance_ledger(client):
    return get_json(client, "/farm/finance-ledger")["transactions"]


def find_finance_row(client, predicate):
    rows = finance_ledger(client)
    for row in rows:
        if predicate(row):
            return row
    raise AssertionError(f"Finance row not found. Rows={rows}")


def simulation_not_milked(client):
    animal_3x = create_animal(
        client,
        "THRICE_DAILY",
        "EDGE-NM-3X",
    )
    animal_2x = create_animal(
        client,
        "TWICE_DAILY",
        "EDGE-NM-2X",
    )

    result = post_json(
        client,
        "/farm/milk/not-milked",
        {
            "milking_session": "MORNING",
            "reason": "POWER_OUTAGE",
            "operational_date": DAY_1.isoformat(),
            "notes": "Synthetic edge-case simulation.",
            "operator": "EDGE-SIM",
        },
    )

    assert result["status"] == "NOT_MILKED"

    next_3x = get_json(
        client,
        f"/farm/milk/next-session"
        f"?animal_id={animal_3x}"
        f"&operational_date={DAY_1.isoformat()}",
    )

    next_2x = get_json(
        client,
        f"/farm/milk/next-session"
        f"?animal_id={animal_2x}"
        f"&operational_date={DAY_1.isoformat()}",
    )

    assert next_3x["next_session"] == "AFTERNOON"
    assert next_2x["next_session"] == "EVENING"

    print("[NOT-MILKED] PASS — farm-level skipped MORNING settles correctly")


def simulation_out_of_order(client):
    animal = create_animal(
        client,
        "THRICE_DAILY",
        "EDGE-ORDER",
    )

    response = client.post(
        "/farm/milk",
        json={
            "animal_id": animal,
            "production_date": DAY_1.isoformat(),
            "milking_session": "EVENING",
            "evening_yield": 6.0,
            "operator": "EDGE-SIM",
        },
    )

    assert response.status_code == 409
    payload = response.json()["detail"]

    assert payload["error"] == "MILKING_SESSION_OUT_OF_SEQUENCE"
    assert payload["next_session"] == "MORNING"
    assert "RECORD_SESSION" in {
        item["action"] for item in payload["resolutions"]
    }
    assert "DECLARE_NOT_MILKED" in {
        item["action"] for item in payload["resolutions"]
    }

    print("[OUT-OF-ORDER] PASS — evening blocked until earlier session settled")


def simulation_date_isolation(client):
    animal = create_animal(
        client,
        "TWICE_DAILY",
        "EDGE-DATES",
    )

    record_milk(client, animal, "MORNING", 10.0, DAY_2)
    record_milk(client, animal, "EVENING", 8.0, DAY_2)

    record_milk(client, animal, "MORNING", 9.0, DAY_1)
    record_milk(client, animal, "EVENING", 7.0, DAY_1)

    recon_1 = get_json(
        client,
        f"/farm/milk/reconciliation"
        f"?production_date={DAY_1.isoformat()}",
    )

    recon_2 = get_json(
        client,
        f"/farm/milk/reconciliation"
        f"?production_date={DAY_2.isoformat()}",
    )

    assert float(recon_1["produced_litres"]) == 16.0
    assert float(recon_2["produced_litres"]) == 18.0

    ledger_1 = get_json(
        client,
        f"/farm/milk/ledger"
        f"?start_date={DAY_1.isoformat()}&end_date={DAY_1.isoformat()}",
    )

    ledger_2 = get_json(
        client,
        f"/farm/milk/ledger"
        f"?start_date={DAY_2.isoformat()}&end_date={DAY_2.isoformat()}",
    )

    assert len(ledger_1["production"]) == 1
    assert len(ledger_2["production"]) == 1

    assert float(ledger_1["production"][0]["total_yield"]) == 16.0
    assert float(ledger_2["production"][0]["total_yield"]) == 18.0

    print("[DATE ISOLATION] PASS — independent daily production state")


def simulation_disposition_void(client):
    animal = create_animal(
        client,
        "TWICE_DAILY",
        "EDGE-DISP-VOID",
    )

    record_milk(client, animal, "MORNING", 10.0, DAY_1)
    record_milk(client, animal, "EVENING", 8.0, DAY_1)

    disposition = post_json(
        client,
        "/farm/milk/dispositions",
        {
            "production_date": DAY_1.isoformat(),
            "disposition_type": "DOMESTIC_USE",
            "quantity_litres": 5.0,
        },
    )

    disposition_id = disposition["id"]

    recon_before = get_json(
        client,
        f"/farm/milk/reconciliation"
        f"?production_date={DAY_1.isoformat()}",
    )

    assert float(recon_before["non_sale_accounted_litres"]) == 5.0

    voided = post_json(
        client,
        f"/farm/milk/dispositions/{disposition_id}/void",
        {"reason": "EDGE-SIM-VOID"},
    )

    assert voided["id"] == disposition_id
    assert voided["status"] == "VOID"

    ledger = get_json(
        client,
        f"/farm/milk/ledger"
        f"?start_date={DAY_1.isoformat()}&end_date={DAY_1.isoformat()}",
    )

    row = next(
        row
        for row in ledger["dispositions"]
        if row["id"] == disposition_id
    )

    assert row["status"] == "VOID"

    recon_after = get_json(
        client,
        f"/farm/milk/reconciliation"
        f"?production_date={DAY_1.isoformat()}",
    )

    assert float(recon_after["non_sale_accounted_litres"]) == 0.0
    assert float(recon_after["unaccounted_litres"]) == 18.0

    print("[DISPOSITION VOID] PASS — retained VOID excluded from totals")


def simulation_finance_sale_void(client):
    animal = create_animal(
        client,
        "TWICE_DAILY",
        "EDGE-FIN-VOID",
    )

    record_milk(client, animal, "MORNING", 10.0, DAY_1)
    record_milk(client, animal, "EVENING", 8.0, DAY_1)

    sale = post_json(
        client,
        "/farm/finance-ledger",
        {
            "transaction_type": "RECEIPT",
            "amount": 2250,
            "quantity": 10,
            "category": "MILK_SALES",
            "payment_method": "CASH",
            "status": "RECEIVED",
            "transaction_date": DAY_1.isoformat(),
        },
    )

    sale_id = sale["id"]

    recon_before = get_json(
        client,
        f"/farm/milk/reconciliation"
        f"?production_date={DAY_1.isoformat()}",
    )

    assert float(recon_before["sold_litres"]) == 10.0
    assert float(recon_before["unaccounted_litres"]) == 8.0

    voided = post_json(
        client,
        f"/farm/finance-ledger/{sale_id}/status",
        {
            "status": "VOID",
            "reason": "EDGE-SIM-VOID",
        },
    )

    assert voided["status"] == "VOID"

    recon_after = get_json(
        client,
        f"/farm/milk/reconciliation"
        f"?production_date={DAY_1.isoformat()}",
    )

    assert float(recon_after["sold_litres"]) == 0.0
    assert float(recon_after["unaccounted_litres"]) == 18.0

    persisted = find_finance_row(
        client,
        lambda row: row["id"] == sale_id,
    )

    assert persisted["status"] == "VOID"

    print("[FINANCE MILK SALE VOID] PASS — sale retained and excluded")


def simulation_feed_opex_void(client):
    feed = post_json(
        client,
        "/farm/finance-ledger",
        {
            "transaction_type": "EXPENSE",
            "master_category": "FEED",
            "sub_category": "Commercial Compound Vanda / Cattle Feed",
            "quantity": 100,
            "unit": "kg",
            "unit_rate": 80,
            "amount": 8000,
            "transaction_date": DAY_1.isoformat(),
            "payment_method": "CASH",
            "status": "PAID",
        },
    )

    opex = post_json(
        client,
        "/farm/finance-ledger",
        {
            "transaction_type": "EXPENSE",
            "master_category": "OPEX",
            "sub_category": "Grid Electricity (WAPDA)",
            "amount": 2500,
            "transaction_date": DAY_1.isoformat(),
            "payment_method": "CASH",
            "status": "PAID",
        },
    )

    feed_id = feed["id"]
    opex_id = opex["id"]

    feed_void = post_json(
        client,
        f"/farm/finance-ledger/{feed_id}/status",
        {
            "status": "VOID",
            "reason": "EDGE-SIM-FEED-VOID",
        },
    )

    opex_void = post_json(
        client,
        f"/farm/finance-ledger/{opex_id}/status",
        {
            "status": "VOID",
            "reason": "EDGE-SIM-OPEX-VOID",
        },
    )

    assert feed_void["status"] == "VOID"
    assert opex_void["status"] == "VOID"

    rows = finance_ledger(client)

    feed_rows = [
        row
        for row in rows
        if row.get("id") == feed_id
    ]
    opex_rows = [
        row
        for row in rows
        if row.get("id") == opex_id
    ]

    assert len(feed_rows) == 1
    assert len(opex_rows) == 1
    assert feed_rows[0]["status"] == "VOID"
    assert opex_rows[0]["status"] == "VOID"

    active_feed = sum(
        float(row["amount"])
        for row in rows
        if row.get("master_category") == "FEED"
        and row["status"] != "VOID"
    )

    active_opex = sum(
        float(row["amount"])
        for row in rows
        if row.get("master_category") == "OPEX"
        and row["status"] != "VOID"
    )

    assert active_feed == 0.0
    assert active_opex == 0.0

    print("[FEED/OPEX VOID] PASS — both categories exclude VOID rows")


def simulation_quality(client):
    payload = post_json(
        client,
        "/farm/milk/quality",
        {
            "quality_date": DAY_1.isoformat(),
            "fat_pct": 3.8,
            "snf_pct": 8.7,
            "sample_type": "BULK_TANK",
            "recorded_by": "EDGE-SIM",
            "notes": "Synthetic quality record.",
        },
    )

    assert payload["data_status"] == "LIVE_PERSISTED_DATA"

    sample = payload["sample"]

    assert float(sample["fat_pct"]) == 3.8
    assert float(sample["snf_pct"]) == 8.7
    assert sample["sample_type"] == "BULK_TANK"
    assert sample["status"] == "RECORDED"

    quality_summary = get_json(
        client,
        f"/farm/milk/quality-summary"
        f"?start_date={DAY_1.isoformat()}"
        f"&end_date={DAY_1.isoformat()}",
    )

    assert quality_summary["sample_count"] == 1
    assert float(quality_summary["average_fat_pct"]) == 3.8
    assert float(quality_summary["average_snf_pct"]) == 8.7

    latest = quality_summary["latest_sample"]

    assert latest["id"] == sample["id"]
    assert float(latest["fat_pct"]) == 3.8
    assert float(latest["snf_pct"]) == 8.7

    quality_list = get_json(
        client,
        f"/farm/milk/quality"
        f"?start_date={DAY_1.isoformat()}"
        f"&end_date={DAY_1.isoformat()}",
    )

    assert len(quality_list["samples"]) == 1
    assert quality_list["samples"][0]["id"] == sample["id"]

    print(
        "[MILK QUALITY] PASS — persisted sample, list, "
        "and summary are consistent"
    )


def simulation_passport_after_operations(client):
    animal = create_animal(
        client,
        "TWICE_DAILY",
        "EDGE-PASSPORT-OPS",
    )

    record_milk(client, animal, "MORNING", 10.0, DAY_1)
    record_milk(client, animal, "EVENING", 8.0, DAY_1)

    passport = get_json(
        client,
        f"/farm/animals/{animal}/passport",
    )

    trace = get_json(
        client,
        f"/farm/milk/{animal}/traceability",
    )

    assert passport
    assert trace["animal"]["animal_id"] == animal
    assert trace["record_count"] == 1
    assert float(trace["total_litres"]) == 18.0

    print("[PASSPORT AFTER OPERATIONS] PASS — identity remains coherent")


def simulation_multi_animal_same_session(client):
    animals = [
        create_animal(
            client,
            "TWICE_DAILY",
            "EDGE-MULTI-01",
        ),
        create_animal(
            client,
            "TWICE_DAILY",
            "EDGE-MULTI-02",
        ),
        create_animal(
            client,
            "THRICE_DAILY",
            "EDGE-MULTI-03",
        ),
    ]

    for index, animal in enumerate(animals):
        litres = 8.0 + index
        next_session = get_json(
            client,
            f"/farm/milk/next-session"
            f"?animal_id={animal}"
            f"&operational_date={DAY_1.isoformat()}",
        )

        assert next_session["next_session"] == "MORNING"

        record_milk(
            client,
            animal,
            "MORNING",
            litres,
            DAY_1,
        )

    for animal, expected in (
        (animals[0], "EVENING"),
        (animals[1], "EVENING"),
        (animals[2], "AFTERNOON"),
    ):
        next_session = get_json(
            client,
            f"/farm/milk/next-session"
            f"?animal_id={animal}"
            f"&operational_date={DAY_1.isoformat()}",
        )

        assert next_session["next_session"] == expected

    print("[MULTI-ANIMAL SESSION] PASS — same-session entries remain isolated")


def run():
    simulations = [
        ("NOT-MILKED", simulation_not_milked),
        ("OUT-OF-ORDER", simulation_out_of_order),
        ("DATE ISOLATION", simulation_date_isolation),
        ("DISPOSITION VOID", simulation_disposition_void),
        ("FINANCE MILK SALE VOID", simulation_finance_sale_void),
        ("FEED/OPEX VOID", simulation_feed_opex_void),
        ("MILK QUALITY", simulation_quality),
        ("PASSPORT AFTER OPERATIONS", simulation_passport_after_operations),
        ("MULTI-ANIMAL SAME SESSION", simulation_multi_animal_same_session),
    ]

    print("=" * 80)
    print("DAIRYOS — EDGE-CASE WORKFLOW SIMULATION SUITE")
    print("=" * 80)
    print()

    passed = 0

    for name, fn in simulations:
        _reset_test_persistence()

        with TestClient(app) as client:
            try:
                fn(client)
                passed += 1
            finally:
                _reset_test_persistence()

    print()
    print("=" * 80)
    print(
        f"EDGE SIMULATION RESULT: "
        f"{passed}/{len(simulations)} scenarios passed"
    )
    print("=" * 80)

    if passed != len(simulations):
        raise SystemExit(1)


if __name__ == "__main__":
    run()
