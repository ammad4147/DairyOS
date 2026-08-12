"""S-09D.55 authoritative operational tab read contract tests."""

from fastapi.testclient import TestClient


EXPECTED_TABS = {
    "animals",
    "milk",
    "feed",
    "health",
    "breeding",
    "workforce",
    "inventory",
    "equipment",
    "finance",
    "analytics",
    "alerts",
}


def test_authoritative_tab_state_contract(client: TestClient):
    response = client.get("/operations/tab-state")

    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["system"] == "DairyOS"
    assert payload["contract_version"] == "S-09D.55"
    assert payload["source"] == "FarmOperationalState"
    assert payload["farm_id"]
    assert payload["operational_date"]
    assert set(payload["tabs"]) == EXPECTED_TABS

    for tab_id in EXPECTED_TABS:
        tab = payload["tabs"][tab_id]
        assert tab["tab_id"] == tab_id
        assert tab["contract_version"] == "S-09D.55"
        assert tab["source"] == "FarmOperationalState"
        assert tab["farm_id"] == payload["farm_id"]
        assert tab["operational_date"] == payload["operational_date"]
        assert tab["status"] in {"ACTIVE", "NO_DATA", "ATTENTION"}
        assert isinstance(tab["state"], dict)


def test_each_tab_has_a_direct_authoritative_read_endpoint(client: TestClient):
    for tab_id in EXPECTED_TABS:
        response = client.get(f"/operations/tab-state/{tab_id}")
        assert response.status_code == 200, (tab_id, response.text)
        payload = response.json()
        assert payload["tab_id"] == tab_id
        assert payload["contract_version"] == "S-09D.55"
        assert payload["source"] == "FarmOperationalState"
        assert isinstance(payload["state"], dict)


def test_unknown_tab_is_rejected(client: TestClient):
    response = client.get("/operations/tab-state/not-a-tab")
    assert response.status_code == 404
    assert "Unknown operational tab" in response.text
