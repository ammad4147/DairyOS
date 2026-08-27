"""Settings: farm identity, reset protection, and deployment control."""


def test_default_settings(client):
    response = client.get("/settings")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["farm_name"] == "Trident Dairies"
    assert body["animal_id_prefix"] == "TD"
    assert body["reset_protected"] is False


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
    assert too_long.status_code == 422, response.text


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


def test_enabling_reset_protection_requires_a_password(client):
    response = client.post("/settings/reset-protection", json={"enabled": True})
    assert response.status_code == 422, response.text


def test_enabling_reset_protection_succeeds_with_a_password(client):
    response = client.post("/settings/reset-protection", json={"enabled": True, "password": "farmSecret1"})
    assert response.status_code == 200, response.text
    assert response.json()["reset_protected"] is True
    assert client.get("/settings").json()["reset_protected"] is True


def test_disabling_reset_protection_needs_no_password(client):
    client.post("/settings/reset-protection", json={"enabled": True, "password": "farmSecret1"})
    response = client.post("/settings/reset-protection", json={"enabled": False})
    assert response.status_code == 200, response.text
    assert response.json()["reset_protected"] is False


def test_reset_requires_literal_confirmation(client):
    response = client.post("/settings/reset", json={"confirm": "yes please", "password": "unused"})
    assert response.status_code == 422, response.text


def test_reset_requires_password_even_when_optional_protection_is_off(client, registered_animal):
    response = client.post("/settings/reset", json={"confirm": "RESET", "password": "anything"})
    assert response.status_code == 403, response.text


def _enable_reset_password(client, password="farmSecret1"):
    response = client.post("/settings/reset-protection", json={"enabled": True, "password": password})
    assert response.status_code == 200, response.text
    return password


def test_reset_wipes_operational_data(client, registered_animal):
    password = _enable_reset_password(client)
    milk = client.post(
        "/farm/milk",
        json={"animal_id": registered_animal, "milking_session": "MORNING", "morning_yield": 20.0, "production_date": "2026-08-13", "operator": "Tester"},
    )
    assert milk.status_code == 200, milk.text
    assert len(client.get("/farm/animals").json()) >= 1

    response = client.post("/settings/reset", json={"confirm": "RESET", "password": password})
    assert response.status_code == 200, response.text
    assert "animal" in response.json()["tables_cleared"]
    assert client.get("/farm/animals").json() == []
    assert client.get("/farm/milk").json() == []


def test_reset_preserves_settings_themselves(client):
    password = _enable_reset_password(client)
    client.put("/settings", json={"farm_name": "Persisted Farm", "animal_id_prefix": "PF"})
    response = client.post("/settings/reset", json={"confirm": "RESET", "password": password})
    assert response.status_code == 200, response.text
    settings = client.get("/settings").json()
    assert settings["farm_name"] == "Persisted Farm"
    assert settings["animal_id_prefix"] == "PF"


def test_reset_blocked_without_correct_password_when_protected(client, registered_animal):
    _enable_reset_password(client, "correct-horse")
    wrong = client.post("/settings/reset", json={"confirm": "RESET", "password": "wrong"})
    assert wrong.status_code == 403, wrong.text
    missing = client.post("/settings/reset", json={"confirm": "RESET"})
    assert missing.status_code == 403, missing.text
    right = client.post("/settings/reset", json={"confirm": "RESET", "password": "correct-horse"})
    assert right.status_code == 200, right.text


def test_reset_after_wipe_new_animal_starts_at_one(client, registered_animal):
    password = _enable_reset_password(client)
    response = client.post("/settings/reset", json={"confirm": "RESET", "password": password})
    assert response.status_code == 200, response.text
    created = client.post("/farm/animals", json={"animal_type": "COW", "lifecycle_status": "HEIFER"}).json()
    assert created["animal_id"] == "TD-001"


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
    assert "reset_protected" in body


def test_deployment_activation_requires_password_and_literal_confirmation(client):
    _enable_reset_password(client, "deploySecret")
    wrong_confirmation = client.post("/settings/deployment/activate", json={"confirm": "YES", "password": "deploySecret"})
    assert wrong_confirmation.status_code == 422, wrong_confirmation.text
    wrong_password = client.post("/settings/deployment/activate", json={"confirm": "DEPLOY", "password": "wrong"})
    assert wrong_password.status_code == 403, wrong_password.text
    deployed = client.post("/settings/deployment/activate", json={"confirm": "DEPLOY", "password": "deploySecret"})
    assert deployed.status_code == 200, deployed.text
    assert deployed.json()["deployment"]["deployed"] is True
