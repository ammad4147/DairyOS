from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from dairyos.domain.milk.repository import MilkRepositoryInterface
from dairyos.domain.milk.entity import MilkProduction
from dairyos.data.database.models.milk_model import MilkProductionORM

class SQLAlchemyMilkRepository(MilkRepositoryInterface):
    def __init__(self, session: Session):
        self._session = session

    def add(self, record: MilkProduction) -> None:
        orm_model = MilkProductionORM(
            id=record.id,
            animal_id=record.animal_id,
            yield_liters=record.yield_liters,
            milking_time=record.milking_time,
            operator_id=record.operator_id,
            recorded_at=record.recorded_at
        )
        self._session.add(orm_model)

    def get_by_id(self, record_id: UUID) -> Optional[MilkProduction]:
        orm_model = self._session.query(MilkProductionORM).filter_by(id=record_id).first()
        if not orm_model:
            return None
        return MilkProduction(
            id=orm_model.id,
            animal_id=orm_model.animal_id,
            yield_liters=orm_model.yield_liters,
            milking_time=orm_model.milking_time,
            operator_id=orm_model.operator_id,
            recorded_at=orm_model.recorded_at
        )
