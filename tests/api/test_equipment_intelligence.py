"""Equipment operational-intelligence wiring (Phase 1, 2026-08-14).

These tests exercise the public equipment entry point and verify that the
resulting governed equipment state reaches the same operational decision
queue used by the Command Center.
"""


def _bind_runtime_operations(container):
    """Keep command-center/decision services on the test's current runtime state."""
    container.runtime._operational_input_projection_bridge.state_service = (
        container.runtime._operational_state_service
    )
    container.operational_command_center_service.operational_state_service = (
        container.runtime._operational_state_service
    )
    container.operational_command_center_service.operational_decision_service.operational_state_service = (
        container.runtime._operational_state_service
    )
    container.operational_decision_service.operational_state_service = (
        container.runtime._operational_state_service
    )


def _record_equipment(client, **overrides):
    from dairyos.app import container

    _bind_runtime_operations(container)
    payload = {
        "equipment_id": "MILK-MACHINE-01",
        "activity": "Routine check",
        "status": "AVAILABLE",
        "operator": "Farm Manager",
    }
    payload.update(overrides)
    response = client.post("/farm/equipment", json=payload)
    assert response.status_code == 200, response.text
    return response


def _decision_titles(client):
    body = client.get("/command-center").json()
    return [item["title"] for item in body["decisions"]["items"]]


def test_out_of_service_equipment_reaches_the_attention_queue(client):
    """A real OUT_OF_SERVICE entry reaches the operator decision queue."""
    _record_equipment(client, equipment_id="TRACTOR-01", status="OUT_OF_SERVICE")

    titles = _decision_titles(client)
    assert any("TRACTOR-01" in title for title in titles), titles


def test_available_equipment_does_not_reach_the_attention_queue(client):
    _record_equipment(client, equipment_id="TRACTOR-02", status="AVAILABLE")

    titles = _decision_titles(client)
    assert not any("TRACTOR-02" in title for title in titles), titles


def test_in_use_and_maintenance_do_not_yet_reach_the_attention_queue(client):
    """MAINTENANCE alone is not an attention condition without due-date evidence."""
    _record_equipment(client, equipment_id="TRACTOR-03", status="IN_USE")
    _record_equipment(client, equipment_id="TRACTOR-04", status="MAINTENANCE")

    titles = _decision_titles(client)
    assert not any("TRACTOR-03" in title for title in titles), titles
    assert not any("TRACTOR-04" in title for title in titles), titles


def test_every_advertised_equipment_state_is_accepted(client):
    from dairyos.api.reference_data import GOVERNED

    for index, status in enumerate(GOVERNED["equipment_states"]):
        _record_equipment(client, equipment_id=f"EQ-GOV-{index}", status=status)
