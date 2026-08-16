"""Settings: farm identity, reset protection, and test-data reset (2026-08-14).

Farm identity backs the short, farm-branded Animal ID scheme (D, 2026-08-14
Settings decision) -- see test_animal_registration_uses_configured_prefix
for the integration proof that a changed prefix actually reaches
`POST /farm/animals`. Reset protection and the reset action itself are the
operator-facing side of "clean all test entries" plus a pre-deployment
password gate.
"""


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
    assert too_long.status_code == 422, too_long.text


def test_blank_farm_name_is_rejected(client):
    response = client.put("/settings", json={"farm_name": "   "})
    assert response.status_code == 422, response.text


# ---------------------------------------------------------------------------
# Animal ID prefix integration
# ---------------------------------------------------------------------------


def test_animal_registration_uses_configured_prefix(client):
    client.put("/settings", json={"animal_id_prefix": "GV"})

    created = client.post(
        "/farm/animals",
        json={"animal_type": "COW", "breed": "Sahiwal", "lifecycle_status": "HEIFER"},
    )
    assert created.status_code == 200, created.text
    assert created.json()["animal_id"].startswith("GV-")


def test_animal_ids_increment_sequentially(client):
    first = client.post("/farm/animals", json={"animal_type": "COW", "lifecycle_status": "HEIFER"}).json()
    second = client.post("/farm/animals", json={"animal_type": "COW", "lifecycle_status": "HEIFER"}).json()

    first_seq = int(first["animal_id"].rsplit("-", 1)[1])
    second_seq = int(second["animal_id"].rsplit("-", 1)[1])
    assert second_seq == first_seq + 1


# ---------------------------------------------------------------------------
# Reset protection
# ---------------------------------------------------------------------------


def test_enabling_reset_protection_requires_a_password(client):
    response = client.post("/settings/reset-protection", json={"enabled": True})
    assert response.status_code == 422, response.text


def test_enabling_reset_protection_succeeds_with_a_password(client):
    response = client.post("/settings/reset-protection", json={"enabled": True, "password": "farmSecret1"})
    assert response.status_code == 200, response.text
    assert response.json()["reset_protected"] is True

    settings = client.get("/settings").json()
    assert settings["reset_protected"] is True


def test_disabling_reset_protection_needs_no_password(client):
    client.post("/settings/reset-protection", json={"enabled": True, "password": "farmSecret1"})
    response = client.post("/settings/reset-protection", json={"enabled": False})
    assert response.status_code == 200, response.text
    assert response.json()["reset_protected"] is False


# ---------------------------------------------------------------------------
# Reset test data
# ---------------------------------------------------------------------------


def test_reset_requires_the_literal_confirm_string(client, registered_animal):
    response = client.post("/settings/reset-test-data", json={"confirm": "yes please"})
    assert response.status_code == 422, response.text


def test_reset_wipes_operational_data(client, registered_animal):
    milk = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "milking_session": "MORNING",
            "morning_yield": 20.0,
            "production_date": "2026-08-13",
            "operator": "Tester",
        },
    )
    assert milk.status_code == 200, milk.text

    before = client.get("/farm/animals").json()
    assert len(before) >= 1

    response = client.post("/settings/reset-test-data", json={"confirm": "RESET"})
    assert response.status_code == 200, response.text
    assert "animal" in response.json()["tables_cleared"]

    after_animals = client.get("/farm/animals").json()
    assert after_animals == []

    after_milk = client.get("/farm/milk").json()
    assert after_milk == []


def test_reset_preserves_settings_themselves(client):
    client.put("/settings", json={"farm_name": "Persisted Farm", "animal_id_prefix": "PF"})
    client.post("/settings/reset-test-data", json={"confirm": "RESET"})

    settings = client.get("/settings").json()
    assert settings["farm_name"] == "Persisted Farm"
    assert settings["animal_id_prefix"] == "PF"


def test_reset_blocked_without_correct_password_when_protected(client, registered_animal):
    client.post("/settings/reset-protection", json={"enabled": True, "password": "correct-horse"})

    wrong = client.post("/settings/reset-test-data", json={"confirm": "RESET", "password": "wrong"})
    assert wrong.status_code == 403, wrong.text

    missing = client.post("/settings/reset-test-data", json={"confirm": "RESET"})
    assert missing.status_code == 403, missing.text

    right = client.post("/settings/reset-test-data", json={"confirm": "RESET", "password": "correct-horse"})
    assert right.status_code == 200, right.text


def test_reset_after_wipe_new_animal_starts_at_one(client, registered_animal):
    client.post("/settings/reset-test-data", json={"confirm": "RESET"})

    created = client.post("/farm/animals", json={"animal_type": "COW", "lifecycle_status": "HEIFER"}).json()
    assert created["animal_id"] == "TD-001"
def test_operational_settings_are_persisted(client):
    response = client.put(
        "/settings/operational",
        json={
            "timezone": "UTC",
            "operational_date_convention": "FARM_LOCAL_DATE",
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["timezone"] == "UTC"
    assert (
        body["operational_date_convention"]
        == "FARM_LOCAL_DATE"
    )
    assert body["current_operational_date"]


def test_invalid_operational_timezone_is_rejected(client):
    response = client.put(
        "/settings/operational",
        json={
            "timezone": "NOT/A_REAL_TIMEZONE",
        },
    )

    assert response.status_code == 422, response.text


def test_dashboard_preferences_are_persisted(client):
    response = client.put(
        "/settings/dashboard",
        json={
            "default_trend_period": "30d",
            "card_visibility": {
                "milk": True,
                "finance": False,
            },
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert (
        body["dashboard"]["default_trend_period"]
        == "30d"
    )
    assert (
        body["dashboard"]["card_visibility"]["finance"]
        is False
    )


def test_invalid_dashboard_period_is_rejected(client):
    response = client.put(
        "/settings/dashboard",
        json={
            "default_trend_period": "today",
        },
    )

    assert response.status_code == 422, response.text


def test_alert_preferences_are_persisted(client):
    response = client.put(
        "/settings/alerts",
        json={
            "preferences": {
                "show_milk_findings": True,
            }
        },
    )

    assert response.status_code == 200, response.text

    assert (
        response.json()["alerts"]["show_milk_findings"]
        is True
    )

