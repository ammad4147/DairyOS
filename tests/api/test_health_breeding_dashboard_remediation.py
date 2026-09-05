from datetime import date
from tests.helpers.breeding import post_breeding


def _animal(client, ear_tag):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "animal_category": "Heifer",
            "ear_tag": ear_tag,
            "breed": "Sahiwal",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["animal_id"]


def test_open_health_case_is_live_on_dashboard(client):
    animal_id = _animal(client, "DASH-HEALTH-OPEN-001")
    health_case = client.post(
        "/farm/health-cases",
        json={
            "animal_id": animal_id,
            "diagnosis": "Mastitis",
            "severity": "SEVERE",
            "operator": "AUDIT-VET",
        },
    )
    assert health_case.status_code == 200, health_case.text
    assert health_case.json()["status"] == "OPEN"

    observation = client.post(
        "/farm/health-observations",
        json={
            "animal_id": animal_id,
            "observation": "Clinical mastitis suspected",
            "severity": "SEVERE",
            "health_case_id": health_case.json()["id"],
            "operator": "AUDIT-VET",
        },
    )
    assert observation.status_code == 200, observation.text

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    health = dashboard.json()["health"]
    assert health["sick"] >= 1
    assert health["mastitis"] >= 1
    assert health["openCases"] >= 1
    assert health["data_status"] == "LIVE_PERSISTED_DATA"


def test_insemination_is_live_on_dashboard(client):
    animal_id = _animal(client, "DASH-BREEDING-AI-001")
    response = post_breeding(
        client,
        animal_id,
        "insemination",
        "COMPLETED",
        technician="AUDIT-TECH",
        timestamp=date.today().isoformat(),
        operator="AUDIT-TECH",
    )
    assert response.status_code == 200, response.text

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    reproduction = dashboard.json()["reproduction"]
    assert reproduction["inseminated"] >= 1
    assert reproduction["pregnancyRatio"] == 0.0
    assert (
        reproduction["pregnancy_ratio_percent"]
        == reproduction["pregnancyRatio"]
    )
    assert reproduction["data_status"] == "LIVE_PERSISTED_DATA"


def test_vaccination_is_live_on_dashboard(client):
    animal_id = _animal(client, "DASH-HEALTH-VAX-001")
    response = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "2 ml",
            "administered_date": date.today().isoformat(),
            "next_due_date": date.today().isoformat(),
            "batch_number": "FMD-AUDIT-001",
            "veterinarian": "AUDIT-VET",
            "operator": "AUDIT-VET",
        },
    )
    assert response.status_code == 200, response.text

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    health = dashboard.json()["health"]
    assert health["completedVax"] >= 1
    assert health["completed_vaccinations"] == health["completedVax"]
    assert health["dueVax"] >= 1
    assert health["due_vaccinations"] == health["dueVax"]
    assert health["data_status"] == "LIVE_PERSISTED_DATA"
