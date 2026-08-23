from datetime import date

from fastapi.testclient import TestClient

from dairyos.app import app, container
from tests.conftest import _reset_test_persistence


TODAY = date.today().isoformat()


def check(response, *expected):
    if response.status_code not in expected:
        raise AssertionError(
            f"{response.request.method} {response.request.url} "
            f"returned {response.status_code}: {response.text}"
        )
    return response


def json_get(client, path):
    return check(client.get(path), 200).json()


def json_post(client, path, payload, *expected):
    return check(client.post(path, json=payload), *(expected or (200, 201))).json()


def find_status_routes():
    routes = []

    for route in app.routes:
        path = getattr(route, "path", "")
        methods = set(getattr(route, "methods", set()) or set())

        if (
            path.startswith("/farm/milk/")
            and path.endswith("/status")
            and ("POST" in methods or "PATCH" in methods)
        ):
            routes.append((path, methods))

    return routes


def void_production(client, production_id):
    response = client.post(
        f"/farm/milk/production/{production_id}/void",
        json={"reason": "MILK-CYCLE-SIM"},
    )

    if response.status_code not in (200, 201):
        raise AssertionError(
            f"POST {response.request.url} returned "
            f"{response.status_code}: {response.text}"
        )

    return response.json()


def main():
    print("=" * 72)
    print("DAIRYOS — COMPLETE MILK CYCLE SIMULATION")
    print("=" * 72)
    print("Synthetic data only.")
    print("Uses FastAPI TestClient and the test persistence reset boundary.")
    print()

    with TestClient(app) as client:
        # ------------------------------------------------------------
        # CLEAN START
        # ------------------------------------------------------------
        _reset_test_persistence()

        health = json_get(client, "/health")
        assert health["status"] == "healthy"
        print("[1/10] API health........................ PASS")

        # ------------------------------------------------------------
        # CREATE SYNTHETIC MILKING ANIMAL
        # ------------------------------------------------------------
        animal = json_post(
            client,
            "/farm/animals",
            {
                "animal_type": "COW",
                "breed": "SIM-SAHIWAL",
                "lifecycle_status": "LACTATING",
                "is_currently_milking": True,
                "milking_frequency": "THRICE_DAILY",
                "ear_tag": "SIM-MILK-CYCLE",
            },
        )

        animal_id = animal["animal_id"]
        print(
            f"[2/10] Synthetic milking animal......... PASS ({animal_id})"
        )

        # ------------------------------------------------------------
        # THREE MILKING SESSIONS
        # ------------------------------------------------------------
        entries = []

        for session, litres in (
            ("MORNING", 8.0),
            ("AFTERNOON", 7.0),
            ("EVENING", 6.0),
        ):
            next_session = json_get(
                client,
                f"/farm/milk/next-session"
                f"?animal_id={animal_id}"
                f"&operational_date={TODAY}",
            )

            actual = next_session.get("next_session")

            assert actual == session, (
                f"Expected next session {session}, got {actual}. "
                f"Payload={next_session}"
            )

            payload = {
                "animal_id": animal_id,
                "milking_session": actual,
                "morning_yield": (
                    litres if actual == "MORNING" else None
                ),
                "afternoon_yield": (
                    litres if actual == "AFTERNOON" else None
                ),
                "evening_yield": (
                    litres if actual == "EVENING" else None
                ),
                "production_date": TODAY,
                "notes": None,
                "operator": "MILK-CYCLE-SIM",
            }

            row = json_post(
                client,
                "/farm/milk",
                payload,
            )

            entries.append(row)

        assert len(entries) == 3
        print(
            "[3/10] Morning + Afternoon + Evening.... PASS "
            "(8 + 7 + 6 = 21.0 L)"
        )

        # ------------------------------------------------------------
        # DAILY LEDGER
        # ------------------------------------------------------------
        ledger = json_get(
            client,
            f"/farm/milk/ledger"
            f"?start_date={TODAY}&end_date={TODAY}",
        )

        rows = [
            row
            for row in ledger["production"]
            if row["animal_id"] == animal_id
        ]

        active_rows = [
            row
            for row in rows
            if row["status"] != "VOID"
        ]

        produced = sum(
            float(row.get("total_yield") or 0)
            for row in active_rows
        )

        assert active_rows, (
            "No active Milk ledger row was produced."
        )

        assert produced == 21.0, (
            f"Expected 21.0 L in the daily Milk ledger, "
            f"got {produced} L. Rows={active_rows}"
        )

        print(
            "[4/10] Daily production ledger.......... PASS "
            "(daily aggregate = 21.0 L)"
        )

        # ------------------------------------------------------------
        # NON-SALE ACCOUNTING
        # ------------------------------------------------------------
        dispositions = (
            ("DOMESTIC_USE", 5.0),
            ("CALF_FEED", 3.0),
            ("WASTAGE", 2.0),
        )

        for disposition_type, litres in dispositions:
            json_post(
                client,
                "/farm/milk/dispositions",
                {
                    "production_date": TODAY,
                    "disposition_type": disposition_type,
                    "quantity_litres": litres,
                    "counterparty": None,
                    "selling_price_per_litre": None,
                    "amount_due": 0,
                    "amount_received": 0,
                    "notes": "MILK-CYCLE-SIM",
                    "operator": "MILK-CYCLE-SIM",
                },
            )

        print(
            "[5/10] Domestic + Calf Feed + Wastage... PASS "
            "(5 + 3 + 2 = 10.0 L)"
        )

        # ------------------------------------------------------------
        # MILK SALE VIA FINANCE
        # ------------------------------------------------------------
        json_post(
            client,
            "/farm/finance-ledger",
            {
                "transaction_type": "RECEIPT",
                "amount": 2475,
                "quantity": 11,
                "category": "MILK_SALES",
                "payment_method": "CASH",
                "status": "RECEIVED",
                "transaction_date": TODAY,
            },
        )

        print(
            "[6/10] Finance milk sale................ PASS "
            "(11.0 L / PKR 2,475)"
        )

        # ------------------------------------------------------------
        # RECONCILIATION
        # ------------------------------------------------------------
        recon = json_get(
            client,
            f"/farm/milk/reconciliation"
            f"?production_date={TODAY}",
        )

        assert float(recon["produced_litres"]) == 21.0
        assert float(recon["sold_litres"]) == 11.0
        assert float(recon["non_sale_accounted_litres"]) == 10.0
        assert float(recon["accounted_litres"]) == 21.0

        unaccounted = float(
            recon["unaccounted_litres"] or 0
        )
        over_accounted = float(
            recon["over_accounted_litres"] or 0
        )

        assert unaccounted == 0.0
        assert over_accounted == 0.0

        print(
            "[7/10] Produced-vs-accounted reconciliation PASS "
            "(21 = 11 + 5 + 3 + 2; 0.0 L unaccounted)"
        )

        # ------------------------------------------------------------
        # VOID ONE SESSION
        # ------------------------------------------------------------
        # The production POST returns an event payload rather than the
        # database ledger-row id. Resolve the persisted daily Milk row first.
        ledger_before_void = json_get(
            client,
            f"/farm/milk/ledger"
            f"?start_date={TODAY}&end_date={TODAY}",
        )

        matching_rows = [
            row
            for row in ledger_before_void["production"]
            if row["animal_id"] == animal_id
        ]

        assert matching_rows, (
            "No persisted Milk ledger row was found for the synthetic animal."
        )

        assert len(matching_rows) == 1, (
            "Expected one daily aggregate Milk ledger row, "
            f"found {len(matching_rows)}."
        )

        production_id = matching_rows[0]["id"]

        void_result = void_production(
            client,
            production_id,
        )

        assert void_result is not None

        ledger_after_void = json_get(
            client,
            f"/farm/milk/ledger"
            f"?start_date={TODAY}&end_date={TODAY}",
        )

        void_rows = [
            row
            for row in ledger_after_void["production"]
            if row["id"] == production_id
        ]

        assert len(void_rows) == 1
        assert void_rows[0]["status"] == "VOID"

        print(
            "[8/10] Void behavior................... PASS "
            "(daily row retained as VOID)"
        )

        # ------------------------------------------------------------
        # VERIFY VOID EXCLUSION FROM TOTALS
        # ------------------------------------------------------------
        recon_after_void = json_get(
            client,
            f"/farm/milk/reconciliation"
            f"?production_date={TODAY}",
        )

        assert recon_after_void["production_complete"] is False
        assert recon_after_void["produced_litres"] is None
        assert float(
            recon_after_void["accounted_litres"]
        ) == 10.0
        assert float(
            recon_after_void["sold_litres"]
        ) == 0.0
        assert float(
            recon_after_void["non_sale_accounted_litres"]
        ) == 10.0

        print(
            "[9/10] Void excluded from totals........ PASS "
            "(daily Milk production row excluded)"
        )

        # ------------------------------------------------------------
        # RELOAD LEDGER AND ENSURE ONLY EXPECTED ACTIVE ROWS REMAIN
        # ------------------------------------------------------------
        final_ledger = json_get(
            client,
            f"/farm/milk/ledger"
            f"?start_date={TODAY}&end_date={TODAY}",
        )

        final_rows = [
            row
            for row in final_ledger["production"]
            if row["animal_id"] == animal_id
        ]

        assert len(final_rows) == 1
        assert final_rows[0]["status"] == "VOID"
        assert final_rows[0]["total_yield"] is None
        assert final_rows[0]["morning_yield"] is None
        assert final_rows[0]["afternoon_yield"] is None
        assert final_rows[0]["evening_yield"] is None

        print(
            "[10/10] Register persistence........... PASS "
            "(daily aggregate retained as VOID)"
        )

        # ------------------------------------------------------------
        # CLEAN UP
        # ------------------------------------------------------------
        _reset_test_persistence()

    print()
    print("=" * 72)
    print("MILK CYCLE SIMULATION: PASS")
    print("=" * 72)
    print()
    print("Synthetic cycle:")
    print("  Production........ 8 + 7 + 6 = 21.0 L")
    print("  Finance sale..... 11.0 L")
    print("  Domestic use...... 5.0 L")
    print("  Calf feed......... 3.0 L")
    print("  Wastage........... 2.0 L")
    print("  Accounted........ 21.0 L")
    print("  Unaccounted....... 0.0 L")
    print("  Void test......... 21.0 L daily aggregate row retained / excluded")
    print()
    print("No live farm data should remain after the final reset.")


if __name__ == "__main__":
    main()
