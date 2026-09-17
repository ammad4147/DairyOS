"""Every report must run on an empty farm without crashing or leaking."""

import pytest

from dairyos.reporting.registry import REPORTS

REQUIRES_ANIMAL = {d.id for d in REPORTS if any(f.required for f in d.filters)}


@pytest.mark.parametrize("report_id", [d.id for d in REPORTS])
def test_report_runs_on_empty_farm(client, report_id):
    response = client.post("/farm/reports/run", json={"report_id": report_id})
    if report_id in REQUIRES_ANIMAL:
        assert response.status_code == 422, response.text
        assert "required" in response.json()["detail"]
        return
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["report"]["id"] == report_id
    assert body["sections"], "a report always presents at least one section"
    assert sum(1 for s in body["sections"] if s["primary"]) == 1
    text = response.text
    assert "undefined" not in text and "photo_data" not in text


@pytest.mark.parametrize("fmt", ["PDF", "XLSX", "CSV"])
@pytest.mark.parametrize("report_id", [d.id for d in REPORTS if d.id not in REQUIRES_ANIMAL])
def test_export_with_no_records(client, report_id, fmt):
    response = client.post(f"/farm/reports/export?format={fmt}", json={"report_id": report_id})
    assert response.status_code == 200, response.text
    assert len(response.content) > 50
    assert response.headers["X-DairyOS-Report-Id"] == report_id
