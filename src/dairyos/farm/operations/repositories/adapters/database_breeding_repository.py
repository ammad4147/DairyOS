"""
Sprint-039

PostgreSQL adapter for operational breeding persistence.

Implements the existing farm.operations repository contract.
"""

from dairyos.farm.operations.repositories.breeding_repository import (
    BreedingRepository,
)

from dairyos.farm.operations.models.breeding_record import (
    BreedingRecord,
)

from dairyos.data.database.models.breeding_record_model import (
    BreedingRecordModel,
)


class DatabaseBreedingRepository(
    BreedingRepository,
):
    """
    SQLAlchemy implementation of breeding persistence.

    A successful save is a durable operational write. Commit here, as
    the other operational repositories do, so a subsequent repository
    session (including the lifetime Animal Passport projection) can
    observe the breeding record immediately.
    """

    def __init__(
        self,
        session,
    ):
        self.session = session

    def save(
        self,
        record: BreedingRecord,
        *,
        commit: bool = True,
    ):
        model = BreedingRecordModel(
            record_id=record.record_id,
            animal_id=record.animal_id,
            event_type=record.event_type,
            result=record.result,
            technician=record.technician,
            semen_or_bull=record.semen_or_bull,
            notes=record.notes,
            semen_lot_id=record.semen_lot_id,
            semen_supplier=record.semen_supplier,
            semen_batch_number=record.semen_batch_number,
            semen_unit_cost=record.semen_unit_cost,
            timestamp=record.timestamp,
        )

        self.session.add(model)
        self.session.flush()
        if commit:
            self.session.commit()
            self.session.refresh(model)

        return record

    def get_all(
        self,
    ) -> list[BreedingRecord]:
        rows = (
            self.session
            .query(BreedingRecordModel)
            .all()
        )

        return [
            BreedingRecord(
                animal_id=row.animal_id,
                event_type=row.event_type,
                result=row.result,
                technician=row.technician,
                semen_or_bull=row.semen_or_bull,
                notes=row.notes,
                semen_lot_id=row.semen_lot_id,
                semen_supplier=row.semen_supplier,
                semen_batch_number=row.semen_batch_number,
                semen_unit_cost=float(row.semen_unit_cost) if row.semen_unit_cost is not None else None,
                record_id=row.record_id,
                timestamp=row.timestamp,
            )
            for row in rows
        ]

    def get_by_animal_id(
        self,
        animal_id: str,
    ) -> list[BreedingRecord]:
        """Fetch one animal's breeding history in the database."""
        if not animal_id:
            return []

        rows = (
            self.session
            .query(BreedingRecordModel)
            .filter(BreedingRecordModel.animal_id == str(animal_id))
            .order_by(BreedingRecordModel.timestamp.asc())
            .all()
        )

        return [
            BreedingRecord(
                animal_id=row.animal_id,
                event_type=row.event_type,
                result=row.result,
                technician=row.technician,
                semen_or_bull=row.semen_or_bull,
                notes=row.notes,
                semen_lot_id=row.semen_lot_id,
                semen_supplier=row.semen_supplier,
                semen_batch_number=row.semen_batch_number,
                semen_unit_cost=float(row.semen_unit_cost) if row.semen_unit_cost is not None else None,
                record_id=row.record_id,
                timestamp=row.timestamp,
            )
            for row in rows
        ]
