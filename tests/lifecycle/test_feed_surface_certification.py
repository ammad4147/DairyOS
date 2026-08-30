import uuid


def _assert_ok(response, method: str, path: str):
    assert response.status_code == 200, (
        f"{method} {path} failed with "
        f"{response.status_code}: {response.text}"
    )
    return response


def _list_from(payload, *keys):
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value

    return []


def _numeric(payload, *keys, default=None):
    if not isinstance(payload, dict):
        return default

    for key in keys:
        value = payload.get(key)
        if value is not None:
            return float(value)

    return default


def test_complete_feed_surface_certification(
    client,
    registered_animal,
):
    feed_item = (
        f"FEED-SURFACE-SILAGE-"
        f"{uuid.uuid4().hex[:8].upper()}"
    )

    # ==============================================================
    # SURFACE 1 — INVENTORY ITEM MASTER
    # ==============================================================

    created = client.post(
        "/farm/feed-inventory/items",
        json={
            "item": feed_item,
            "category": "FEED",
            "unit": "kg",
            "location": "Bunker 1",
            "reorder_level": 200.0,
            "active": True,
            "notes": "Feed surface certification",
        },
    )

    _assert_ok(
        created,
        "POST",
        "/farm/feed-inventory/items",
    )

    created_payload = created.json()

    assert created_payload["item"] == feed_item
    assert created_payload["unit"] == "kg"

    # ==============================================================
    # SURFACE 2 — INVENTORY RECEIPT
    # ==============================================================

    purchase = client.post(
        "/farm/feed-inventory/movements",
        json={
            "item": feed_item,
            "quantity": 1000.0,
            "movement_type": "PURCHASE",
            "unit": "kg",
            "location": "Bunker 1",
            "supplier": "SURFACE-CERTIFICATION-SUPPLIER",
            "notes": "Initial feed receipt",
            "recorded_by": "Feed Surface Certification",
        },
    )

    _assert_ok(
        purchase,
        "POST",
        "/farm/feed-inventory/movements",
    )

    purchase_payload = purchase.json()

    assert purchase_payload["item"] == feed_item
    assert float(purchase_payload["quantity"]) == 1000.0
    assert purchase_payload["movement_type"] == "PURCHASE"

    # ==============================================================
    # SURFACE 3 — INVENTORY CONSUMPTION
    # ==============================================================

    consumption = client.post(
        "/farm/feed-inventory/movements",
        json={
            "item": feed_item,
            "quantity": 250.0,
            "movement_type": "CONSUMPTION",
            "unit": "kg",
            "location": "Bunker 1",
            "notes": "Operational consumption",
            "recorded_by": "Feed Surface Certification",
        },
    )

    _assert_ok(
        consumption,
        "POST",
        "/farm/feed-inventory/movements",
    )

    consumption_payload = consumption.json()

    assert consumption_payload["item"] == feed_item
    assert float(consumption_payload["quantity"]) == 250.0
    assert consumption_payload["movement_type"] == "CONSUMPTION"

    expected_balance = 750.0

    # ==============================================================
    # SURFACE 4 — INVENTORY DASHBOARD
    # ==============================================================

    inventory_dashboard = client.get(
        "/farm/feed-inventory/dashboard"
    )

    _assert_ok(
        inventory_dashboard,
        "GET",
        "/farm/feed-inventory/dashboard",
    )

    inventory_dashboard_payload = (
        inventory_dashboard.json()
    )

    assert (
        inventory_dashboard_payload["data_status"]
        == "LIVE_PERSISTED_DATA"
    )

    inventory_items = _list_from(
        inventory_dashboard_payload,
        "items",
    )

    inventory_row = next(
        (
            row
            for row in inventory_items
            if row.get("item") == feed_item
        ),
        None,
    )

    assert inventory_row is not None

    assert float(
        inventory_row["balance"]
    ) == expected_balance

    # ==============================================================
    # SURFACE 5 — INVENTORY MOVEMENT HISTORY
    # ==============================================================

    movements = client.get(
        "/farm/feed-inventory/movements",
        params={"item": feed_item},
    )

    _assert_ok(
        movements,
        "GET",
        "/farm/feed-inventory/movements",
    )

    movement_rows = _list_from(
        movements.json(),
        "movements",
    )

    matching_movements = [
        row
        for row in movement_rows
        if row.get("item") == feed_item
    ]

    assert len(matching_movements) >= 2

    assert any(
        row.get("movement_type") == "PURCHASE"
        and float(row.get("quantity") or 0.0) == 1000.0
        for row in matching_movements
    )

    assert any(
        row.get("movement_type") == "CONSUMPTION"
        and float(row.get("quantity") or 0.0) == 250.0
        for row in matching_movements
    )

    # ==============================================================
    # SURFACE 6 — AUTHORITATIVE INVENTORY PROJECTION
    # ==============================================================

    authoritative = client.get(
        "/farm/feed-inventory/authoritative"
    )

    _assert_ok(
        authoritative,
        "GET",
        "/farm/feed-inventory/authoritative",
    )

    authoritative_payload = authoritative.json()

    assert (
        authoritative_payload["data_status"]
        == "LIVE_PERSISTED_DATA"
    )

    authoritative_items = _list_from(
        authoritative_payload,
        "items",
    )

    authoritative_row = next(
        (
            row
            for row in authoritative_items
            if row.get("item") == feed_item
        ),
        None,
    )

    assert authoritative_row is not None

    assert float(
        authoritative_row["balance"]
    ) == expected_balance

    # ==============================================================
    # SURFACE 7 — GOVERNED ANIMAL FEED RECORD
    # ==============================================================

    governed_feed = client.post(
        "/farm/feed/records",
        json={
            "animal_id": registered_animal,
            "feed_type": "SILAGE",
            "quantity_kg": 18.5,
            "notes": "Feed surface certification",
        },
    )

    _assert_ok(
        governed_feed,
        "POST",
        "/farm/feed/records",
    )

    governed_payload = governed_feed.json()

    assert governed_payload["animal_id"] == registered_animal
    assert governed_payload["feed_type"] == "SILAGE"
    assert float(
        governed_payload["quantity_kg"]
    ) == 18.5

    assert (
        governed_payload["data_status"]
        == "LIVE_PERSISTED_DATA"
    )

    # ==============================================================
    # SURFACE 8 — GOVERNED FEED HISTORY
    # ==============================================================

    governed_history = client.get(
        "/farm/feed/records"
    )

    _assert_ok(
        governed_history,
        "GET",
        "/farm/feed/records",
    )

    governed_rows = _list_from(
        governed_history.json(),
        "records",
    )

    assert any(
        row.get("animal_id") == registered_animal
        and row.get("feed_type") == "SILAGE"
        and float(
            row.get("quantity_kg") or 0.0
        ) == 18.5
        for row in governed_rows
    )

    # ==============================================================
    # SURFACE 9 — FEED OVERVIEW
    # ==============================================================

    overview = client.get(
        "/farm/feed/overview"
    )

    _assert_ok(
        overview,
        "GET",
        "/farm/feed/overview",
    )

    overview_payload = overview.json()

    assert (
        overview_payload["data_status"]
        == "LIVE_PERSISTED_DATA"
    )

    assert (
        int(
            overview_payload["feeding_records"]
        )
        >= 1
    )

    assert (
        float(
            overview_payload[
                "total_recorded_feed_kg"
            ]
        )
        >= 18.5
    )

    # ==============================================================
    # SURFACE 10 — BASIC FARM FEED ENTRY
    # ==============================================================

    basic_feed = client.post(
        "/farm/feed",
        json={
            "feed_type": "Silage",
            "quantity_kg": 12.0,
            "operator": "Feed Surface Certification",
            "animal_id": registered_animal,
        },
    )

    _assert_ok(
        basic_feed,
        "POST",
        "/farm/feed",
    )

    basic_payload = basic_feed.json()

    assert basic_payload["feed_type"] == "Silage"
    assert float(
        basic_payload["quantity_kg"]
    ) == 12.0
    assert (
        basic_payload["operator"]
        == "Feed Surface Certification"
    )

    basic_history = client.get(
        "/farm/feed"
    )

    _assert_ok(
        basic_history,
        "GET",
        "/farm/feed",
    )

    basic_rows = _list_from(
        basic_history.json(),
        "feed",
        "records",
        "items",
        "data",
    )

    assert any(
        row.get("feed_type") == "Silage"
        and float(
            row.get("quantity_kg") or 0.0
        ) == 12.0
        for row in basic_rows
    )

    # ==============================================================
    # SURFACE 11 — RATION
    # ==============================================================

    ration_name = (
        "Feed Surface Certification "
        f"Ration {uuid.uuid4().hex[:8].upper()}"
    )

    ration = client.post(
        "/farm/feed/rations",
        json={
            "name": ration_name,
            "animal_group": "LACTATING",
            "ingredients": [
                {
                    "feed_type": "SILAGE",
                    "quantity_kg": 18.0,
                },
                {
                    "feed_type": "SOYBEAN_MEAL",
                    "quantity_kg": 2.0,
                },
            ],
            "target_dmi_kg": 22.0,
            "dry_matter_pct": 42.0,
            "crude_protein_pct": 16.5,
            "ndf_pct": 30.0,
            "energy_mcal_kg": 1.55,
            "cost_per_kg": 0.42,
            "effective_date": "2026-08-30",
            "operator": "Feed Surface Certification",
        },
    )

    _assert_ok(
        ration,
        "POST",
        "/farm/feed/rations",
    )

    ration_payload = ration.json()

    assert ration_payload["name"] == ration_name
    assert (
        ration_payload["animal_group"]
        == "LACTATING"
    )

    assert (
        ration_payload["data_status"]
        == "LIVE_PERSISTED_DATA"
    )

    ration_history = client.get(
        "/farm/feed/rations",
        params={"animal_group": "LACTATING"},
    )

    _assert_ok(
        ration_history,
        "GET",
        "/farm/feed/rations?animal_group=LACTATING",
    )

    ration_rows = _list_from(
        ration_history.json(),
        "rations",
        "items",
        "data",
    )

    assert any(
        row.get("name") == ration_name
        for row in ration_rows
    )

    # ==============================================================
    # SURFACE 12 — DASHBOARD
    # ==============================================================

    dashboard = client.get(
        "/dashboard"
    )

    _assert_ok(
        dashboard,
        "GET",
        "/dashboard",
    )

    dashboard_payload = dashboard.json()

    assert "dashboard" in dashboard_payload
    assert isinstance(
        dashboard_payload["dashboard"],
        dict,
    )

    dashboard_feed = dashboard_payload[
        "dashboard"
    ].get("feed")

    assert isinstance(
        dashboard_feed,
        dict,
    ), (
        "Dashboard does not expose its established "
        "dashboard.feed projection."
    )

    assert "today_kg" in dashboard_feed
    assert "events" in dashboard_feed
    assert "last_feed_type" in dashboard_feed

    print()
    print("=" * 78)
    print("DAIRYOS FEED SURFACE CERTIFICATION")
    print("=" * 78)
    print(
        "Inventory opening balance:",
        0.0,
        "kg",
    )
    print(
        "Inventory purchase:",
        1000.0,
        "kg",
    )
    print(
        "Inventory consumption:",
        250.0,
        "kg",
    )
    print(
        "Inventory expected closing:",
        expected_balance,
        "kg",
    )
    print(
        "Inventory dashboard:",
        inventory_row["balance"],
        "kg",
    )
    print(
        "Authoritative projection:",
        authoritative_row["balance"],
        "kg",
    )
    print(
        "Governed animal feed:",
        governed_payload["quantity_kg"],
        "kg",
    )
    print(
        "Feed overview total:",
        overview_payload[
            "total_recorded_feed_kg"
        ],
        "kg",
    )
    print(
        "Dashboard feed:",
        dashboard_feed,
    )

    # ==============================================================
    # Dashboard propagation contract
    # ==============================================================

    assert float(
        dashboard_feed["today_kg"] or 0.0
    ) >= 18.5, (
        "Dashboard feed.today_kg did not propagate the "
        "persisted governed Feed record."
    )

    assert int(
        dashboard_feed["events"] or 0
    ) >= 1, (
        "Dashboard feed.events did not propagate the "
        "persisted governed Feed record."
    )

    assert str(
        dashboard_feed["last_feed_type"] or ""
    ).upper() == "SILAGE", (
        "Dashboard feed.last_feed_type did not propagate "
        "the persisted governed Feed record."
    )

    # ==============================================================
    # SURFACE 13 — RELOAD / PERSISTENCE
    # ==============================================================

    reloaded_inventory = client.get(
        "/farm/feed-inventory/dashboard"
    )

    _assert_ok(
        reloaded_inventory,
        "GET",
        "/farm/feed-inventory/dashboard",
    )

    reloaded_items = _list_from(
        reloaded_inventory.json(),
        "items",
    )

    reloaded_item = next(
        (
            row
            for row in reloaded_items
            if row.get("item") == feed_item
        ),
        None,
    )

    assert reloaded_item is not None

    assert float(
        reloaded_item["balance"]
    ) == expected_balance

    reloaded_records = client.get(
        "/farm/feed/records"
    )

    _assert_ok(
        reloaded_records,
        "GET",
        "/farm/feed/records",
    )

    reloaded_record_rows = _list_from(
        reloaded_records.json(),
        "records",
    )

    assert any(
        row.get("animal_id") == registered_animal
        and row.get("feed_type") == "SILAGE"
        and float(
            row.get("quantity_kg") or 0.0
        ) == 18.5
        for row in reloaded_record_rows
    )

    print(
        "Reload inventory balance:",
        reloaded_item["balance"],
        "kg",
    )
    print(
        "Reload governed Feed record: PASS"
    )
    print("=" * 78)
    print(
        "COMPLETE FEED SURFACE CERTIFICATION: PASS"
    )
    print("=" * 78)
