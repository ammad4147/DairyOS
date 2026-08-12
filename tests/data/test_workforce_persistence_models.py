from dairyos.data.database.base import Base
from dairyos.data.database.models.workforce_model import (
    OperationalShiftModel,
    WorkScheduleModel,
    WorkShiftModel,
)


def test_workforce_tables_are_registered():
    assert WorkScheduleModel.__tablename__ in Base.metadata.tables
    assert WorkShiftModel.__tablename__ in Base.metadata.tables
    assert OperationalShiftModel.__tablename__ in Base.metadata.tables


def test_work_shift_belongs_to_schedule():
    foreign_keys = WorkShiftModel.__table__.c.schedule_id.foreign_keys
    assert any(fk.target_fullname == "work_schedules.schedule_id" for fk in foreign_keys)
