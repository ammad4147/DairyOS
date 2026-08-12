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

    A successful save is a durable operational write.  Commit here, as
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
    ):
        model = BreedingRecordModel(
            record_id=record.record_id,
            animal_id=record.animal_id,
            event_type=record.event_type,
            result=record.result,
            technician=record.technician,
            timestamp=record.timestamp,
        )

        self.session.add(model)
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
                record_id=row.record_id,
                timestamp=row.timestamp,
            )
            for row in rows
        ]
