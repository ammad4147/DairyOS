"""Fixtures for Reporting certification on a disposable database."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests import conftest as root
from tests.reporting import synthetic_farm
from dairyos.reporting.registry import REPORT_BY_ID


def _clear_official_coml(container) -> None:
    """COML records are outside the root reset list; remove them row by row
    (the database guard rejects multi-row deletes)."""
    from dairyos.data.models.coml_record import COMLRecord

    session = container.repository_factory.session
    session.rollback()
    for row in session.query(COMLRecord).all():
        session.delete(row)
        session.flush()
    session.commit()


@pytest.fixture(scope="module")
def farm(tmp_path_factory):
    """A seeded synthetic farm with the farm clock frozen at 18-Sep-2026.

    Module scoped: the farm is written once and only read afterwards, so the
    certification modules stay fast. The root ``client`` fixture resets the
    disposable database again before any later test.
    """
    from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService
    from dairyos.farm.herd.repository.animal_operational_state_repository import AnimalOperationalStateRepository
    from dairyos.farm.herd.services.animal_event_projection import AnimalEventProjection
    from dairyos.runtime.persistent_event_journal import PersistentEventJournal

    patcher = pytest.MonkeyPatch()
    patcher.setattr(FarmSettingsService, "get_operational_datetime", lambda self: synthetic_farm.NOW)

    container = root.container
    root._clear_test_event_journal()
    container.event_journal = PersistentEventJournal()
    container.animal_operational_state_repository = AnimalOperationalStateRepository(
        storage_path=tmp_path_factory.mktemp("reporting") / "animal_operational_states.json")
    container.animal_event_projection = AnimalEventProjection(repository=container.animal_operational_state_repository)
    container.started = False

    with TestClient(root.app) as client:
        root._reset_test_persistence()
        _clear_official_coml(container)
        handles = synthetic_farm.seed(container.repository_factory.session)
        for animal_id, body in (
            (synthetic_farm.EXITED_DEAD, {"disposition": "DECEASED", "effective_date": "2026-09-08",
                                          "cause": "Bloat", "veterinarian": "Dr. Hamid", "operator": "Test"}),
            (synthetic_farm.EXITED_SOLD, {"disposition": "SOLD", "effective_date": "2026-09-10", "amount": 150000,
                                          "buyer_or_counterparty": "Rana Livestock", "operator": "Test"}),
        ):
            response = client.patch(f"/farm/animals/{animal_id}/disposition", json=body)
            assert response.status_code == 200, response.text
        client.handles = handles
        try:
            yield client
        finally:
            _clear_official_coml(container)
            patcher.undo()


@pytest.fixture(scope="module")
def run(farm):
    def _run(report_id: str, *, period=None, filters=None, expect=200, **extra):
        # Certification reads every catalogue column unless a test asks for a
        # specific selection; default-column behaviour has its own tests.
        catalogue = REPORT_BY_ID[report_id].columns
        if "columns" not in extra and catalogue:
            extra["columns"] = [column.key for column in catalogue]
        elif extra.get("columns") == "default":
            extra.pop("columns")
        response = farm.post("/farm/reports/run", json={
            "report_id": report_id, "period": period or {}, "filters": filters or {}, "page_size": 500, **extra})
        assert response.status_code == expect, response.text
        return response.json()
    return _run


def section(body: dict, section_id: str) -> dict:
    return next(s for s in body["sections"] if s["id"] == section_id)


def metric(body: dict, key: str):
    return next(m["value"] for m in body["summary"] if m["key"] == key)
