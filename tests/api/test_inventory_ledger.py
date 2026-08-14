"""Inventory ledger (G8.1, 2026-08-14).

Before this, `POST /farm/inventory` was event-journal-only -- no queryable
stock model existed, so nothing could answer "how much feed is left"
without hand-replaying the event journal. Direction of the six real
movement types (`GET /farm/reference-data`'s `inventory_movement_types`) is
fixed by decision, confirmed via AskUserQuestion 2026-08-14: PURCHASE/
RECEIPT always increase stock, CONSUMPTION/WASTAGE always decrease it,
TRANSFER/ADJUSTMENT carry an operator-entered signed quantity since neither
type's direction is implied by its name alone.
"""

from dairyos.api.reference_data import GOVERNED


def _record_inventory(client, **overrides):
    payload = {
        "item": "Silage",
        "quantity": 100.0,
        "movement_type": "PURCHASE",
        "unit": "kg",
        "operator": "Farm Manager",
    }
    payload.update(overrides)
    return client.post("/farm/inventory", json=payload)


def _balance(client, item):
    body = client.get("/farm/inventory/balance").json()
    return body["items"].get(item)


# ---------------------------------------------------------------------------
# Direction per governed movement type
# ---------------------------------------------------------------------------


def test_purchase_increases_balance(client):
    response = _record_inventory(client, item="Silage-A", quantity=100.0, movement_type="PURCHASE")
    assert response.status_code == 200, response.text

    assert _balance(client, "Silage-A")["balance"] == 100.0


def test_receipt_increases_balance(client):
    _record_inventory(client, item="Silage-B", quantity=50.0, movement_type="RECEIPT")

    assert _balance(client, "Silage-B")["balance"] == 50.0


def test_consumption_decreases_balance(client):
    _record_inventory(client, item="Silage-C", quantity=100.0, movement_type="PURCHASE")
    _record_inventory(client, item="Silage-C", quantity=30.0, movement_type="CONSUMPTION")

    assert _balance(client, "Silage-C")["balance"] == 70.0


def test_wastage_decreases_balance(client):
    _record_inventory(client, item="Silage-D", quantity=100.0, movement_type="PURCHASE")
    _record_inventory(client, item="Silage-D", quantity=5.0, movement_type="WASTAGE")

    assert _balance(client, "Silage-D")["balance"] == 95.0


def test_transfer_direction_is_the_operators_signed_quantity(client):
    _record_inventory(client, item="Silage-E", quantity=100.0, movement_type="PURCHASE")
    # Outbound transfer -- operator enters a negative quantity themselves.
    response = _record_inventory(client, item="Silage-E", quantity=-20.0, movement_type="TRANSFER")
    assert response.status_code == 200, response.text

    assert _balance(client, "Silage-E")["balance"] == 80.0


def test_adjustment_can_correct_up_or_down(client):
    _record_inventory(client, item="Silage-F", quantity=100.0, movement_type="PURCHASE")
    _record_inventory(client, item="Silage-F", quantity=-10.0, movement_type="ADJUSTMENT")
    _record_inventory(client, item="Silage-F", quantity=3.0, movement_type="ADJUSTMENT")

    assert _balance(client, "Silage-F")["balance"] == 93.0


def test_balance_is_independent_per_item(client):
    _record_inventory(client, item="Silage-G1", quantity=100.0, movement_type="PURCHASE")
    _record_inventory(client, item="Silage-G2", quantity=40.0, movement_type="PURCHASE")

    assert _balance(client, "Silage-G1")["balance"] == 100.0
    assert _balance(client, "Silage-G2")["balance"] == 40.0


# ---------------------------------------------------------------------------
# Validation -- the whole point of governing this at all
# ---------------------------------------------------------------------------


def test_purchase_with_nonpositive_quantity_is_rejected(client):
    response = _record_inventory(client, item="Silage-H", quantity=-5.0, movement_type="PURCHASE")
    assert response.status_code == 422, response.text
    assert _balance(client, "Silage-H") is None


def test_consumption_with_zero_quantity_is_rejected(client):
    response = _record_inventory(client, item="Silage-I", quantity=0.0, movement_type="CONSUMPTION")
    assert response.status_code == 422, response.text


def test_transfer_with_zero_quantity_is_rejected(client):
    """Zero has no direction -- TRANSFER/ADJUSTMENT need a nonzero signed value."""
    response = _record_inventory(client, item="Silage-J", quantity=0.0, movement_type="TRANSFER")
    assert response.status_code == 422, response.text


def test_unlisted_movement_type_is_rejected(client):
    response = _record_inventory(client, item="Silage-K", quantity=10.0, movement_type="RESTOCK")
    assert response.status_code == 422, response.text
    assert _balance(client, "Silage-K") is None


def test_every_advertised_movement_type_is_accepted(client):
    for index, movement_type in enumerate(GOVERNED["inventory_movement_types"]):
        quantity = -5.0 if movement_type in ("TRANSFER", "ADJUSTMENT") else 5.0
        response = _record_inventory(
            client,
            item=f"Item-{index}",
            quantity=quantity,
            movement_type=movement_type,
        )
        assert response.status_code == 200, response.text
