from dairyos.api.app import app


def test_record_milk_entry(client, registered_animal):
    response = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 8.0,
            "afternoon_yield": 7.5,
            "evening_yield": 6.5,
            "operator": "Milking Operator",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["animal_id"] == registered_animal
    assert body["total_yield"] == 22.0
    assert body["status"] == "RECORDED"
    assert body["operator"] == "Milking Operator"


def test_list_milk_entries(client, registered_animal):
    client.post("/farm/milk", json={"animal_id": registered_animal, "morning_yield": 5.0, "operator": "Milking Operator"})
    response = client.get("/farm/milk")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_record_feed_entry(client):
    response = client.post("/farm/feed", json={"feed_type": "Silage", "quantity_kg": 20.0, "group_or_pen": "Pen B", "operator": "Feed Supervisor"})
    assert response.status_code == 200
    body = response.json()
    assert body["feed_type"] == "Silage"
    assert body["quantity_kg"] == 20.0
    assert body["operator"] == "Feed Supervisor"


def test_list_feed_entries(client):
    response = client.get("/farm/feed")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_record_health_observation(client, registered_animal):
    response = client.post("/farm/health-observations", json={"animal_id": registered_animal, "symptom": "Lethargy", "temperature_c": 39.9, "severity": "ELEVATED", "operator": "Dr Vet"})
    assert response.status_code == 200
    body = response.json()
    assert body["animal_id"] == registered_animal
    assert body["severity"] == "ELEVATED"
    assert body["status"] == "OPEN"
    assert body["operator"] == "Dr Vet"


def test_list_health_observations(client):
    response = client.get("/farm/health-observations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_record_breeding_entry(client, registered_animal):
    response = client.post("/farm/breeding", json={"animal_id": registered_animal, "event_type": "insemination", "technician": "Dr Vet", "result": "completed", "operator": "Dr Vet"})
    assert response.status_code == 200
    body = response.json()
    assert body["animal_id"] == registered_animal
    assert body["event_type"] == "insemination"
    assert body["operator"] == "Dr Vet"


def test_list_breeding_entries(client):
    response = client.get("/farm/breeding")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_record_workforce_entry(client):
    response = client.post("/farm/workforce", json={"worker_id": "WORKER-001", "activity": "milking", "task": "Evening milking", "status": "COMPLETED", "hours": 1.5, "operator": "Farm Supervisor"})
    assert response.status_code == 200
    body = response.json()
    assert body["worker_id"] == "WORKER-001"
    assert body["activity"] == "milking"


def test_list_workforce_entries(client):
    response = client.get("/farm/workforce")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_record_inventory_entry(client):
    response = client.post("/farm/inventory", json={"item": "Silage", "quantity": 440.0, "movement_type": "CONSUMPTION", "unit": "kg", "operator": "Feed Supervisor"})
    assert response.status_code == 200
    body = response.json()
    assert body["item"] == "Silage"
    assert body["quantity"] == 440.0


def test_list_inventory_entries(client):
    response = client.get("/farm/inventory")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_record_equipment_entry(client):
    response = client.post("/farm/equipment", json={"equipment_id": "MILKER-001", "activity": "inspection", "status": "OPERATIONAL", "running_hours": 120.5, "operator": "Maintenance Lead"})
    assert response.status_code == 200
    body = response.json()
    assert body["equipment_id"] == "MILKER-001"
    assert body["activity"] == "inspection"


def test_list_equipment_entries(client):
    response = client.get("/farm/equipment")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_record_financial_entry(client):
    response = client.post("/farm/financial", json={"transaction_type": "EXPENSE", "amount": 25000.0, "category": "FEED", "payment_method": "BANK", "counterparty": "Feed Supplier", "operator": "Farm Manager"})
    assert response.status_code == 200
    body = response.json()
    assert body["transaction_type"] == "EXPENSE"
    assert body["amount"] == 25000.0
    assert body["operator"] == "Farm Manager"


def test_list_financial_entries(client):
    response = client.get("/farm/financial")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
