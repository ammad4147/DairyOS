from __future__ import annotations

from dairyos.data.models.vaccination_record import VaccinationRecord


class VaccinationRepository:
    """Database boundary for authoritative vaccination facts."""

    def __init__(self, session=None):
        self.session = session
        self.records: list[VaccinationRecord] = []

    def add(self, record: VaccinationRecord, *, commit: bool = True):
        if self.session is None:
            self.records.append(record)
            return record
        self.session.add(record)
        self.session.flush()
        if commit and not self.session.info.get("operational_write_managed", False):
            self.session.commit()
            self.session.refresh(record)
        return record

    def get_all(self):
        if self.session is None:
            return list(self.records)
        return (
            self.session.query(VaccinationRecord)
            .order_by(
                VaccinationRecord.administered_date.asc(),
                VaccinationRecord.id.asc(),
            )
            .all()
        )

    def get_for_animal(self, animal_id: str):
        if self.session is None:
            return [
                row for row in self.records
                if row.animal_id == animal_id
            ]
        return (
            self.session.query(VaccinationRecord)
            .filter(VaccinationRecord.animal_id == animal_id)
            .order_by(
                VaccinationRecord.administered_date.asc(),
                VaccinationRecord.id.asc(),
            )
            .all()
        )
