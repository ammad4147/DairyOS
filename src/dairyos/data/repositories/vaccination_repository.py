from __future__ import annotations

from sqlalchemy import func

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

    def get_by_id(self, record_id: int):
        """Return one authoritative vaccination occurrence by primary key."""
        if self.session is None:
            return next(
                (
                    row
                    for row in self.records
                    if getattr(row, "id", None) == record_id
                ),
                None,
            )
        return (
            self.session.query(VaccinationRecord)
            .filter(VaccinationRecord.id == record_id)
            .one_or_none()
        )

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

    def active_duplicate_exists(
        self,
        *,
        animal_id: str,
        vaccine: str,
        scheduled_date,
        exclude_id: int | None = None,
    ) -> bool:
        """Return whether the active schedule already has this occurrence."""
        if self.session is None:
            return any(
                row.animal_id == animal_id
                and str(row.vaccine or "").casefold() == vaccine.casefold()
                and row.next_due_date == scheduled_date
                and str(row.status or "").upper() != "VOID"
                and (
                    exclude_id is None
                    or getattr(row, "id", None) != exclude_id
                )
                for row in self.records
            )

        query = self.session.query(VaccinationRecord).filter(
            VaccinationRecord.animal_id == animal_id,
            func.lower(VaccinationRecord.vaccine) == vaccine.casefold(),
            VaccinationRecord.next_due_date == scheduled_date,
            VaccinationRecord.status != "VOID",
        )
        if exclude_id is not None:
            query = query.filter(VaccinationRecord.id != exclude_id)
        return self.session.query(query.exists()).scalar()

    def amend_scheduled_occurrence(
        self,
        record: VaccinationRecord,
        *,
        vaccine: str,
        dose: str,
        scheduled_date,
        veterinarian: str | None,
        notes: str | None,
        operator: str,
        commit: bool = True,
    ):
        """Amend mutable schedule fields without replacing identity metadata."""
        record.vaccine = vaccine
        record.dose = dose
        record.next_due_date = scheduled_date
        record.veterinarian = veterinarian
        record.notes = notes
        record.operator = operator
        record.schedule_status = "SCHEDULED"

        if self.session is not None:
            self.session.flush()
            if commit and not self.session.info.get(
                "operational_write_managed", False
            ):
                self.session.commit()
                self.session.refresh(record)

        return record

    def void_scheduled_occurrence(
        self,
        record: VaccinationRecord,
        *,
        operator: str,
        notes: str | None = None,
        commit: bool = True,
    ):
        """Logically void a scheduled occurrence without deleting its row."""
        record.status = "VOID"
        record.schedule_status = "VOID"
        record.operator = operator
        if notes is not None:
            record.notes = notes

        if self.session is not None:
            self.session.flush()
            if commit and not self.session.info.get(
                "operational_write_managed", False
            ):
                self.session.commit()
                self.session.refresh(record)

        return record
