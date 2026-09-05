from datetime import date, timedelta
from uuid import uuid4


def ensure_test_semen_lot(
    client,
    *,
    sire_code: str = "TEST-SIRE",
    semen_type: str = "CONVENTIONAL",
    quantity: int = 100,
):
    stock = client.get("/farm/breeding/semen-stock")
    assert stock.status_code == 200, stock.text
    for row in stock.json().get("available_lots", []):
        if row.get("sire_code") == sire_code and row.get("semen_type") == semen_type:
            return row

    batch = f"TEST-{sire_code}-{uuid4().hex[:8].upper()}"
    purchase = client.post(
        "/farm/finance-ledger",
        json={
            "transaction_type": "EXPENSE",
            "master_category": "OPEX",
            "sub_category": "Semen Straws (Sexed / Conventional)",
            "quantity": quantity,
            "unit": "straw",
            "unit_rate": 100,
            "amount": quantity * 100,
            "transaction_date": "2020-01-01",
            "payment_method": "CASH",
            "counterparty": "Test Genetics Supplier",
            "status": "PAID",
            "semen_type": semen_type,
            "sire_code": sire_code,
            "semen_batch_number": batch,
            "semen_storage_location": "TEST-TANK",
        },
    )
    assert purchase.status_code == 200, purchase.text

    stock = client.get("/farm/breeding/semen-stock")
    assert stock.status_code == 200, stock.text
    return next(
        row
        for row in stock.json().get("available_lots", [])
        if row.get("sire_code") == sire_code and row.get("semen_type") == semen_type
    )


def post_breeding(
    client,
    animal_id: str,
    event_type: str,
    result: str,
    **extra,
):
    payload = {
        "animal_id": animal_id,
        "event_type": event_type,
        "technician": "Dr Vet",
        "result": result,
        "operator": "Dr Vet",
        **extra,
    }

    normalized = str(event_type).strip().lower()
    if normalized in {"insemination", "ai", "artificial_insemination"}:
        if payload.get("semen_lot_id") is None:
            requested_sire = str(payload.pop("_test_sire_code", "TEST-SIRE"))
            requested_type = str(payload.pop("_test_semen_type", "CONVENTIONAL"))
            lot = ensure_test_semen_lot(
                client,
                sire_code=requested_sire,
                semen_type=requested_type,
            )
            payload["semen_lot_id"] = lot["id"]

    if normalized in {"calving", "calved", "parturition"}:
        payload.setdefault("calf_sex", "FEMALE")
        payload.setdefault(
            "planned_return_to_milking_date",
            (date.today() + timedelta(days=30)).isoformat(),
        )

    return client.post("/farm/breeding", json=payload)
