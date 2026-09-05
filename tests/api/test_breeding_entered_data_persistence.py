from datetime import date

from sqlalchemy.orm import Session

from dairyos.api import animal_management
from dairyos.api import breeding_biology
from dairyos.data.database.models.breeding_record_model import BreedingRecordModel
from dairyos.data.database.session import engine
from tests.helpers.breeding import post_breeding


def test_live_reproduction_policies_use_one_283_day_gestation_authority():
    assert animal_management.reproduction._POLICY.gestation_days == 283
    assert breeding_biology._POLICY.gestation_days == 283


def test_breeding_entry_persists_entered_sire_notes_and_operational_date(
    client,
    registered_animal,
):
    response = post_breeding(
        client,
        registered_animal,
        "insemination",
        "COMPLETED",
        technician="Dr Vet",
        notes="Operator-entered breeding note",
        operator="Dr Vet",
        timestamp="2026-09-05",
        _test_sire_code="SIRE-283",
        _test_semen_type="SEXED",
    )
    assert response.status_code == 200, response.text
    record_id = response.json()["record_id"]

    with Session(engine) as session:
        row = session.get(BreedingRecordModel, record_id)
        assert row is not None
        assert row.semen_or_bull == "Sexed Semen (90% Female) — SIRE-283"
        assert row.notes == "Operator-entered breeding note"
        assert row.timestamp.date() == date(2026, 9, 5)

    ledger = client.get("/farm/breeding")
    assert ledger.status_code == 200, ledger.text
    persisted = next(
        row for row in ledger.json()
        if row.get("record_id") == record_id
    )
    assert persisted["semen_or_bull"] == "Sexed Semen (90% Female) — SIRE-283"
    assert persisted["notes"] == "Operator-entered breeding note"
