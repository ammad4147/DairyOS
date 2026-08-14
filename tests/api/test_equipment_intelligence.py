"""Equipment operational-intelligence wiring (Phase 1, 2026-08-14).

Two compounding defects made `EquipmentIntelligenceService`'s attention
check structurally unreachable in production, even though its own logic and
its existing unit tests (`tests/farm/operations/services/
test_equipment_operational_state.py`) were fine in isolation.

**Payload-shape bug (found while fixing this).** `FarmOperationalState`'s
`equipment_status_recorded` handler, and the intelligence check downstream
of it, both read `equipment_status[equipment_id]["operational_status"]` out
of a `"details"` sub-object on the event payload. Nothing on the real write
path (`POST /farm/equipment` -> `_record()` -> the operational input
gateway) ever built that sub-object -- the submitted fields sit flat -- so
`event_payload.get("details", {})` always evaluated to `{}` and no
equipment status ever reached the check at all. This is the same class of
defect as G10.4 (financial), just undiscovered for equipment until now.

**Vocabulary mismatch (G9.1, already filed).** Even with the payload
reaching the check, it watched for ATTENTION/FAILED/CRITICAL -- values the
governed `equipment_states` dropdown (AVAILABLE/IN_USE/MAINTENANCE/
OUT_OF_SERVICE) can never produce. Decided 2026-08-13: keep the governed
vocabulary, fix the check to watch for OUT_OF_SERVICE.

Both are fixed together here: neither fix alone would have made the check
reachable by a real operator using the app's own dropdown.
"""


def _record_equipment(client, **overrides):
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
    """The concrete bug: a real operator entry never used to surface at all."""
    _record_equipment(client, equipment_id="TRACTOR-01", status="OUT_OF_SERVICE")

    titles = _decision_titles(client)
    assert any("TRACTOR-01" in title for title in titles), titles


def test_available_equipment_does_not_reach_the_attention_queue(client):
    _record_equipment(client, equipment_id="TRACTOR-02", status="AVAILABLE")

    titles = _decision_titles(client)
    assert not any("TRACTOR-02" in title for title in titles), titles


def test_in_use_and_maintenance_do_not_yet_reach_the_attention_queue(client):
    """MAINTENANCE is not itself an attention condition until next_service_due_at
    (G9.3) exists to say whether it's overdue -- deliberately not invented here.
    """
    _record_equipment(client, equipment_id="TRACTOR-03", status="IN_USE")
    _record_equipment(client, equipment_id="TRACTOR-04", status="MAINTENANCE")

    titles = _decision_titles(client)
    assert not any("TRACTOR-03" in title for title in titles), titles
    assert not any("TRACTOR-04" in title for title in titles), titles


def test_every_advertised_equipment_state_is_accepted(client):
    from dairyos.api.reference_data import GOVERNED

    for index, status in enumerate(GOVERNED["equipment_states"]):
        _record_equipment(client, equipment_id=f"EQ-GOV-{index}", status=status)
