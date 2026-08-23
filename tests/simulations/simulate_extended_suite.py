from datetime import date

from fastapi.testclient import TestClient

from dairyos.app import app
import sys
from pathlib import Path as _Path

ROOT = _Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.conftest import _reset_test_persistence



TODAY = date.today().isoformat()


def check(response, *expected):
    if response.status_code not in expected:
        raise AssertionError(
            f"{response.request.method} {response.request.url} -> "
            f"{response.status_code}: {response.text}"
        )
    return response


def get_json(client, path):
    return check(client.get(path), 200).json()


def post_json(client, path, payload, expected=(200, 201)):
    return check(client.post(path, json=payload), *expected).json()


def create_animal(client, frequency, tag):
    row = post_json(
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
    )
    return row["animal_id"]


def record_session(client, animal_id, session, litres):
    payload = {
        "animal_id": animal_id,
        "milking_session": session,
        "morning_yield": litres if session == "MORNING" else None,
        "afternoon_yield": litres if session == "AFTERNOON" else None,
        "evening_yield": litres if session == "EVENING" else None,
        "production_date": TODAY,
        "operator": "SIM",
    }
    return post_json(client, "/farm/milk", payload)


def simulation_3x(client):
    animal_id = create_animal(client, "THRICE_DAILY", "SIM-3X")

    expected = [
        ("MORNING", 8.0),
        ("AFTERNOON", 7.0),
        ("EVENING", 6.0),
    ]

    for session, litres in expected:
        nxt = get_json(
            client,
            f"/farm/milk/next-session"
            f"?animal_id={animal_id}"
            f"&operational_date={TODAY}",
        )
        assert nxt["next_session"] == session
        record_session(client, animal_id, session, litres)

    ledger = get_json(
        client,
        f"/farm/milk/ledger?start_date={TODAY}&end_date={TODAY}",
    )

    rows = [
        r for r in ledger["production"]
        if r["animal_id"] == animal_id
    ]

    assert len(rows) == 1
    assert float(rows[0]["total_yield"]) == 21.0

    print("[3X] PASS — MORNING/AFTERNOON/EVENING = 21.0 L")


def simulation_2x(client):
    animal_id = create_animal(client, "TWICE_DAILY", "SIM-2X")

    expected = [
        ("MORNING", 10.0),
        ("EVENING", 8.0),
    ]

    for session, litres in expected:
        nxt = get_json(
            client,
            f"/farm/milk/next-session"
            f"?animal_id={animal_id}"
            f"&operational_date={TODAY}",
        )
        assert nxt["next_session"] == session
        record_session(client, animal_id, session, litres)

    # After the two expected sessions, there must be no further session.
    nxt = get_json(
        client,
        f"/farm/milk/next-session"
        f"?animal_id={animal_id}"
        f"&operational_date={TODAY}",
    )

    assert nxt["next_session"] in (None, "COMPLETE", "DONE")

    ledger = get_json(
        client,
        f"/farm/milk/ledger?start_date={TODAY}&end_date={TODAY}",
    )

    rows = [
        r for r in ledger["production"]
        if r["animal_id"] == animal_id
    ]

    assert len(rows) == 1
    assert float(rows[0]["total_yield"]) == 18.0
    assert rows[0]["afternoon_yield"] is None

    print("[2X] PASS — MORNING/EVENING = 18.0 L")


def simulation_combined(client):
    animal_3x = create_animal(
        client,
        "THRICE_DAILY",
        "SIM-COMB-3X",
    )

    animal_2x = create_animal(
        client,
        "TWICE_DAILY",
        "SIM-COMB-2X",
    )

    sessions_3x = {
        "MORNING": 8.0,
        "AFTERNOON": 7.0,
        "EVENING": 6.0,
    }

    sessions_2x = {
        "MORNING": 10.0,
        "EVENING": 8.0,
    }

    # Deliberately interleave two animals with different schedules while
    # respecting each animal's own sequence.
    sequence = [
        (animal_3x, "MORNING", sessions_3x["MORNING"]),
        (animal_2x, "MORNING", sessions_2x["MORNING"]),
        (animal_3x, "AFTERNOON", sessions_3x["AFTERNOON"]),
        (animal_2x, "EVENING", sessions_2x["EVENING"]),
        (animal_3x, "EVENING", sessions_3x["EVENING"]),
    ]

    for animal_id, session, litres in sequence:
        nxt = get_json(
            client,
            f"/farm/milk/next-session"
            f"?animal_id={animal_id}"
            f"&operational_date={TODAY}",
        )

        assert nxt["next_session"] == session, (
            f"{animal_id}: expected {session}, "
            f"got {nxt['next_session']}; payload={nxt}"
        )

        record_session(
            client,
            animal_id,
            session,
            litres,
        )

    # Confirm both animals are now complete for the day.
    nxt_3x = get_json(
        client,
        f"/farm/milk/next-session"
        f"?animal_id={animal_3x}"
        f"&operational_date={TODAY}",
    )

    nxt_2x = get_json(
        client,
        f"/farm/milk/next-session"
        f"?animal_id={animal_2x}"
        f"&operational_date={TODAY}",
    )

    assert nxt_3x["next_session"] is None
    assert nxt_2x["next_session"] is None
    assert nxt_3x["status"] == "DAY_COMPLETE"
    assert nxt_2x["status"] == "DAY_COMPLETE"

    ledger = get_json(
        client,
        f"/farm/milk/ledger"
        f"?start_date={TODAY}&end_date={TODAY}",
    )

    row_3x = next(
        r for r in ledger["production"]
        if r["animal_id"] == animal_3x
    )

    row_2x = next(
        r for r in ledger["production"]
        if r["animal_id"] == animal_2x
    )

    assert float(row_3x["total_yield"]) == 21.0
    assert float(row_2x["total_yield"]) == 18.0

    assert row_3x["morning_yield"] == 8.0
    assert row_3x["afternoon_yield"] == 7.0
    assert row_3x["evening_yield"] == 6.0

    assert row_2x["morning_yield"] == 10.0
    assert row_2x["afternoon_yield"] is None
    assert row_2x["evening_yield"] == 8.0

    print(
        "[COMBINED] PASS — "
        "3X=21.0 L, 2X=18.0 L, "
        "independent animal-specific sequencing"
    )


def simulation_passport(client):
    animal = post_json(
        client,
        "/farm/animals",
        {
            "animal_type": "COW",
            "breed": "SIM-HF",
            "lifecycle_status": "LACTATING",
            "is_currently_milking": True,
            "milking_frequency": "TWICE_DAILY",
            "ear_tag": "SIM-PASSPORT",
        },
    )

    animal_id = animal["animal_id"]

    passport = get_json(
        client,
        f"/farm/animals/{animal_id}/passport",
    )

    assert passport
    assert (
        passport.get("animal", {}).get("animal_id")
        == animal_id
        or passport.get("animal_id") == animal_id
    )

    trace = get_json(
        client,
        f"/farm/milk/{animal_id}/traceability",
    )

    assert trace["animal"]["animal_id"] == animal_id
    assert trace["record_count"] == 0

    print("[PASSPORT] PASS — identity and traceability linked")


def simulation_finance(client):
    # Milk sale
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
            "transaction_date": TODAY,
        },
    )

    assert sale["category"] == "MILK_SALES"
    assert float(sale["quantity"]) == 10.0

    # Feed expense
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
            "transaction_date": TODAY,
            "payment_method": "CASH",
            "status": "PAID",
        },
    )

    assert feed["master_category"] == "FEED"
    assert float(feed["amount"]) == 8000.0

    # OPEX expense
    opex = post_json(
        client,
        "/farm/finance-ledger",
        {
            "transaction_type": "EXPENSE",
            "master_category": "OPEX",
            "sub_category": "Grid Electricity (WAPDA)",
            "amount": 2500,
            "transaction_date": TODAY,
            "payment_method": "CASH",
            "status": "PAID",
        },
    )

    assert opex["master_category"] == "OPEX"
    assert float(opex["amount"]) == 2500.0

    ledger = get_json(
        client,
        "/farm/finance-ledger",
    )

    rows = ledger["transactions"]

    milk_rows = [
        r for r in rows
        if r["category"] == "MILK_SALES"
        and r["status"] != "VOID"
    ]

    feed_rows = [
        r for r in rows
        if r.get("master_category") == "FEED"
        and r["status"] != "VOID"
    ]

    opex_rows = [
        r for r in rows
        if r.get("master_category") == "OPEX"
        and r["status"] != "VOID"
    ]

    assert sum(float(r.get("quantity") or 0) for r in milk_rows) == 10.0
    assert sum(float(r["amount"]) for r in feed_rows) == 8000.0
    assert sum(float(r["amount"]) for r in opex_rows) == 2500.0

    print(
        "[FINANCE] PASS — Milk Sales + FEED + OPEX "
        "persist in unified ledger"
    )


def simulation_cross_module(client):
    animal_id = create_animal(
        client,
        "TWICE_DAILY",
        "SIM-CROSS",
    )

    record_session(
        client,
        animal_id,
        "MORNING",
        10.0,
    )

    record_session(
        client,
        animal_id,
        "EVENING",
        8.0,
    )

    # Account 8 L domestic + 10 L Finance sale.
    post_json(
        client,
        "/farm/milk/dispositions",
        {
            "production_date": TODAY,
            "disposition_type": "DOMESTIC_USE",
            "quantity_litres": 8,
        },
    )

    post_json(
        client,
        "/farm/finance-ledger",
        {
            "transaction_type": "RECEIPT",
            "amount": 2250,
            "quantity": 10,
            "category": "MILK_SALES",
            "payment_method": "CASH",
            "status": "RECEIVED",
            "transaction_date": TODAY,
        },
    )

    recon = get_json(
        client,
        f"/farm/milk/reconciliation?production_date={TODAY}",
    )

    assert recon["production_complete"] is True
    assert float(recon["produced_litres"]) == 18.0
    assert float(recon["sold_litres"]) == 10.0
    assert float(recon["non_sale_accounted_litres"]) == 8.0
    assert float(recon["accounted_litres"]) == 18.0
    assert float(recon["unaccounted_litres"]) == 0.0
    assert recon["status"] == "RECONCILED"

    passport = get_json(
        client,
        f"/farm/animals/{animal_id}/passport",
    )

    assert passport

    print(
        "[CROSS-MODULE] PASS — Animal → Milk → Finance → "
        "Reconciliation = 0.0 L unaccounted"
    )


def run():
    print("=" * 80)
    print("DAIRYOS — EXTENDED CROSS-MODULE SIMULATION SUITE")
    print("=" * 80)
    print()

    simulations = [
        ("Milk 3X", simulation_3x),
        ("Milk 2X", simulation_2x),
        ("Combined 3X + 2X", simulation_combined),
        ("Animal Passport", simulation_passport),
        ("Finance", simulation_finance),
        ("Cross Module", simulation_cross_module),
    ]

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
        f"SIMULATION SUITE RESULT: "
        f"{passed}/{len(simulations)} scenarios passed"
    )
    print("=" * 80)

    if passed != len(simulations):
        raise SystemExit(1)


if __name__ == "__main__":
    run()
