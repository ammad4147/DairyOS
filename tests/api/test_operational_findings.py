"""Operational Finding entity (AA-013 §4, D-UI-5, 2026-08-14).

The single cross-cutting entity behind the dashboard action queue, every
section's alert list, and navigation count badges. Findings are raised by
detection engines (see test_milk_drop_detection.py for the first real
producer), never by a manual POST -- there is deliberately no
`POST /farm/findings`, so these tests raise findings directly through
`OperationalFindingService` (the same call path a detection engine uses)
and then exercise the operator-facing HTTP lifecycle exactly as the
dashboard's Action Queue does.
"""

import re

from dairyos.app import container
from dairyos.farm.findings.services.operational_finding_service import (
    OperationalFindingService,
)

FINDING_ID_PATTERN = re.compile(r"^[A-Z]{2,3}-\d{6}-\d{3}$")


def _service():
    return OperationalFindingService(container.repository_factory.operational_findings())


def _raise_finding(**overrides):
    payload = {
        "source_module": "HEALTH",
        "severity": "HIGH",
        "title": "Test finding",
        "detail": "Detail text",
        "subject_type": "ANIMAL",
        "subject_id": "AN-TEST-001",
        "dedupe_key": "TEST_KEY:AN-TEST-001",
    }
    payload.update(overrides)
    return _service().raise_or_update(**payload)


# ---------------------------------------------------------------------------
# ID allocation (§4.2)
# ---------------------------------------------------------------------------


def test_raising_a_finding_generates_a_governed_id(client):
    finding = _raise_finding()
    assert FINDING_ID_PATTERN.match(finding.finding_id), finding.finding_id
    assert finding.finding_id.startswith("HL-")
    assert finding.status == "RAISED"
    assert finding.observation_count == 1


def test_prefix_matches_source_module(client):
    milk = _raise_finding(source_module="MILK", dedupe_key="TEST_KEY:MILK")
    assert milk.finding_id.startswith("AL-")

    breeding = _raise_finding(source_module="BREEDING", dedupe_key="TEST_KEY:BREEDING")
    assert breeding.finding_id.startswith("BR-")

    inventory = _raise_finding(source_module="INVENTORY", dedupe_key="TEST_KEY:INV")
    assert inventory.finding_id.startswith("INV-")

    equipment = _raise_finding(source_module="EQUIPMENT", dedupe_key="TEST_KEY:EQ")
    assert equipment.finding_id.startswith("EQ-")

    feed = _raise_finding(source_module="FEED", dedupe_key="TEST_KEY:FEED")
    assert feed.finding_id.startswith("FD-")

    workforce = _raise_finding(source_module="WORKFORCE", dedupe_key="TEST_KEY:WF")
    assert workforce.finding_id.startswith("WF-")

    finance = _raise_finding(source_module="FINANCE", dedupe_key="TEST_KEY:FN")
    assert finance.finding_id.startswith("FN-")


def test_sequential_ids_on_the_same_day_increment(client):
    first = _raise_finding(dedupe_key="TEST_KEY:SEQ1")
    second = _raise_finding(dedupe_key="TEST_KEY:SEQ2")
    first_seq = int(first.finding_id.rsplit("-", 1)[1])
    second_seq = int(second.finding_id.rsplit("-", 1)[1])
    assert second_seq == first_seq + 1


# ---------------------------------------------------------------------------
# Dedupe / re-detection lifecycle (§4.4)
# ---------------------------------------------------------------------------


def test_redetection_updates_instead_of_duplicating(client):
    first = _raise_finding(dedupe_key="TEST_KEY:SAME")
    second = _raise_finding(dedupe_key="TEST_KEY:SAME", detail="Updated detail")

    assert first.finding_id == second.finding_id
    assert second.observation_count == 2
    assert second.detail == "Updated detail"


def test_resolved_finding_recurring_raises_new_not_reopened(client):
    first = _raise_finding(dedupe_key="TEST_KEY:RECUR")
    _service().resolve(first.finding_id, operator="Tester", resolution_note="Fixed")

    second = _raise_finding(dedupe_key="TEST_KEY:RECUR")
    assert second.finding_id != first.finding_id


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_unknown_severity_is_rejected(client):
    try:
        _service().raise_or_update(source_module="HEALTH", severity="MILD", title="x")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_unknown_source_module_is_rejected(client):
    try:
        _service().raise_or_update(source_module="NOT_A_MODULE", severity="HIGH", title="x")
        assert False, "expected ValueError"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# HTTP lifecycle -- the same surface the dashboard Action Queue uses
# ---------------------------------------------------------------------------


def test_list_findings_endpoint(client):
    finding = _raise_finding(dedupe_key="TEST_KEY:LIST")
    response = client.get("/farm/findings")
    assert response.status_code == 200, response.text
    ids = [f["finding_id"] for f in response.json()["findings"]]
    assert finding.finding_id in ids


def test_acknowledge_then_resolve(client):
    finding = _raise_finding(dedupe_key="TEST_KEY:ACKRESOLVE")

    ack = client.post(f"/farm/findings/{finding.finding_id}/acknowledge", json={})
    assert ack.status_code == 200, ack.text
    assert ack.json()["status"] == "ACKNOWLEDGED"
    assert ack.json()["acknowledged_by"] == "UI Operator"

    resolve = client.post(
        f"/farm/findings/{finding.finding_id}/resolve",
        json={"resolution_note": "Done"},
    )
    assert resolve.status_code == 200, resolve.text
    assert resolve.json()["status"] == "RESOLVED"


def test_critical_resolve_requires_a_note(client):
    finding = _raise_finding(severity="CRITICAL", dedupe_key="TEST_KEY:CRITRESOLVE")

    missing_note = client.post(f"/farm/findings/{finding.finding_id}/resolve", json={})
    assert missing_note.status_code == 422, missing_note.text

    with_note = client.post(
        f"/farm/findings/{finding.finding_id}/resolve",
        json={"resolution_note": "Vet confirmed recovery"},
    )
    assert with_note.status_code == 200, with_note.text


def test_non_critical_resolve_does_not_require_a_note(client):
    finding = _raise_finding(severity="MONITORING", dedupe_key="TEST_KEY:NONCRIT")
    response = client.post(f"/farm/findings/{finding.finding_id}/resolve", json={})
    assert response.status_code == 200, response.text


def test_acknowledge_unknown_finding_returns_404(client):
    response = client.post("/farm/findings/AL-999999-999/acknowledge", json={})
    assert response.status_code == 404


def test_counts_by_module_endpoint(client):
    _raise_finding(source_module="HEALTH", dedupe_key="TEST_KEY:COUNT1")
    _raise_finding(source_module="HEALTH", dedupe_key="TEST_KEY:COUNT2")
    _raise_finding(source_module="INVENTORY", dedupe_key="TEST_KEY:COUNT3")

    response = client.get("/farm/findings/counts")
    assert response.status_code == 200, response.text
    counts = response.json()["counts"]
    assert counts.get("HEALTH") == 2
    assert counts.get("INVENTORY") == 1


def test_resolved_findings_excluded_from_counts(client):
    finding = _raise_finding(source_module="EQUIPMENT", dedupe_key="TEST_KEY:COUNTRESOLVE")
    client.post(f"/farm/findings/{finding.finding_id}/resolve", json={})

    response = client.get("/farm/findings/counts")
    counts = response.json()["counts"]
    assert counts.get("EQUIPMENT", 0) == 0


def test_module_filter(client):
    _raise_finding(source_module="EQUIPMENT", dedupe_key="TEST_KEY:FILTER1")

    response = client.get("/farm/findings", params={"module": "EQUIPMENT"})
    assert response.status_code == 200, response.text
    findings = response.json()["findings"]
    assert len(findings) >= 1
    assert all(f["source_module"] == "EQUIPMENT" for f in findings)
