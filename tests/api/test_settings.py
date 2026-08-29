"""Settings: farm identity, operational preferences, and deployment control."""


def test_default_settings(client):
    response = client.get("/settings")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["farm_name"] == "Trident Dairies"
    assert body["animal_id_prefix"] == "TD"
    assert "reset_protected" not in body


def test_update_farm_name_and_prefix(client):
    response = client.put("/settings", json={"farm_name": "Green Valley Dairy", "animal_id_prefix": "gv"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["farm_name"] == "Green Valley Dairy"
    assert body["animal_id_prefix"] == "GV"

    refetched = client.get("/settings").json()
    assert refetched["farm_name"] == "Green Valley Dairy"
    assert refetched["animal_id_prefix"] == "GV"


def test_invalid_prefix_is_rejected(client):
    response = client.put("/settings", json={"animal_id_prefix": "12"})
    assert response.status_code == 422, response.text
    too_long = client.put("/settings", json={"animal_id_prefix": "TOOLONG"})
    assert too_long.status_code == 422, too_long.text


def test_blank_farm_name_is_rejected(client):
    response = client.put("/settings", json={"farm_name": "   "})
    assert response.status_code == 422, response.text


def test_animal_registration_uses_configured_prefix(client):
    client.put("/settings", json={"animal_id_prefix": "GV"})
    created = client.post("/farm/animals", json={"animal_type": "COW", "breed": "Sahiwal", "lifecycle_status": "HEIFER"})
    assert created.status_code == 200, created.text
    assert created.json()["animal_id"].startswith("GV-")


def test_animal_ids_increment_sequentially(client):
    first = client.post("/farm/animals", json={"animal_type": "COW", "lifecycle_status": "HEIFER"}).json()
    second = client.post("/farm/animals", json={"animal_type": "COW", "lifecycle_status": "HEIFER"}).json()
    first_seq = int(first["animal_id"].rsplit("-", 1)[1])
    second_seq = int(second["animal_id"].rsplit("-", 1)[1])
    assert second_seq == first_seq + 1


def test_legacy_reset_requires_migration_to_admin_tool(client):
    response = client.post("/settings/reset", json={"confirm": "RESET"})
    assert response.status_code == 410, response.text
    assert "Administration Tool" in response.json()["detail"]


def test_legacy_reset_does_not_wipe_operational_data(client, registered_animal):
    milk = client.post(
        "/farm/milk",
        json={"animal_id": registered_animal, "milking_session": "MORNING", "morning_yield": 20.0, "production_date": "2026-08-13", "operator": "Tester"},
    )
    assert milk.status_code == 200, milk.text
    assert len(client.get("/farm/animals").json()) >= 1

    response = client.post("/settings/reset", json={"confirm": "RESET"})
    assert response.status_code == 410, response.text
    assert len(client.get("/farm/animals").json()) >= 1
    assert client.get("/farm/milk").json() != []


def test_legacy_reset_preserves_settings_and_does_not_mutate_data(client):
    client.put("/settings", json={"farm_name": "Persisted Farm", "animal_id_prefix": "PF"})
    response = client.post("/settings/reset", json={"confirm": "RESET"})
    assert response.status_code == 410, response.text
    settings = client.get("/settings").json()
    assert settings["farm_name"] == "Persisted Farm"
    assert settings["animal_id_prefix"] == "PF"


def test_operational_settings_are_persisted(client):
    response = client.put("/settings/operational", json={"timezone": "UTC", "operational_date_convention": "FARM_LOCAL_DATE"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["timezone"] == "UTC"
    assert body["operational_date_convention"] == "FARM_LOCAL_DATE"
    assert body["current_operational_date"]


def test_invalid_operational_timezone_is_rejected(client):
    response = client.put("/settings/operational", json={"timezone": "NOT/A_REAL_TIMEZONE"})
    assert response.status_code == 422, response.text


def test_dashboard_preferences_are_persisted(client):
    response = client.put("/settings/dashboard", json={"default_trend_period": "30d", "card_visibility": {"milk": True, "finance": False}})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["dashboard"]["default_trend_period"] == "30d"
    assert body["dashboard"]["card_visibility"]["finance"] is False


def test_invalid_dashboard_period_is_rejected(client):
    response = client.put("/settings/dashboard", json={"default_trend_period": "today"})
    assert response.status_code == 422, response.text


def test_alert_preferences_are_persisted(client):
    response = client.put("/settings/alerts", json={"preferences": {"show_milk_findings": True}})
    assert response.status_code == 200, response.text
    assert response.json()["alerts"]["show_milk_findings"] is True


def test_deployment_status_is_available(client):
    response = client.get("/settings/deployment")
    assert response.status_code == 200, response.text
    body = response.json()
    assert "deployed" in body
    assert "reset_protected" not in body


def test_deployment_activation_requires_literal_confirmation_but_no_password(client):
    wrong_confirmation = client.post("/settings/deployment/activate", json={"confirm": "YES"})
    assert wrong_confirmation.status_code == 422, wrong_confirmation.text
    deployed = client.post("/settings/deployment/activate", json={"confirm": "DEPLOY"})
    assert deployed.status_code == 200, deployed.text
    assert deployed.json()["deployment"]["deployed"] is True
