def test_cmp_scenario_can_be_created_and_listed(client):
    response = client.post(
        "/farm/cmp/scenarios",
        json={
            "name": "Current Actual",
            "created_by": "Test Operator",
            "period_start": "2026-08-01",
            "period_end": "2026-08-16",
            "selected_cost_domains": [
                "FEED",
                "LABOUR",
            ],
            "assumptions": {
                "cost_multipliers": {
                    "FEED": 1.25,
                    "LABOUR": 1.0,
                },
                "additional_costs": {},
                "excluded_cost_domains": [],
            },
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["scenario"]["name"] == "Current Actual"
    assert body["evaluation"]["mutates_authoritative_records"] is False

    scenario_id = body["scenario"]["scenario_id"]

    listed = client.get("/farm/cmp/scenarios")

    assert listed.status_code == 200, listed.text
    assert any(
        item["scenario_id"] == scenario_id
        for item in listed.json()["scenarios"]
    )


def test_cmp_scenario_rejects_unknown_cost_domain(client):
    response = client.post(
        "/farm/cmp/scenarios",
        json={
            "name": "Invalid",
            "created_by": "Test Operator",
            "period_start": "2026-08-01",
            "period_end": "2026-08-16",
            "selected_cost_domains": [
                "NOT_A_COST_DOMAIN",
            ],
            "assumptions": {},
        },
    )

    assert response.status_code == 422


def test_cmp_scenario_rejects_negative_assumption(client):
    response = client.post(
        "/farm/cmp/scenarios",
        json={
            "name": "Invalid Negative",
            "created_by": "Test Operator",
            "period_start": "2026-08-01",
            "period_end": "2026-08-16",
            "selected_cost_domains": [
                "FEED",
            ],
            "assumptions": {
                "additional_costs": {
                    "FEED": -1,
                },
            },
        },
    )

    assert response.status_code == 422


def test_unknown_cmp_scenario_returns_404(client):
    response = client.get(
        "/farm/cmp/scenarios/CMP-DOES-NOT-EXIST"
    )

    assert response.status_code == 404
