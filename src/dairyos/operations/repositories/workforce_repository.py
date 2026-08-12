from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from dairyos.data.database.models.workforce_model import (
    OperationalShiftModel,
    WorkScheduleModel,
    WorkShiftModel,
)


class SqlAlchemyWorkforceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_schedule(self, farm_id: str, schedule_id: str):
        return self.db.scalar(
            select(WorkScheduleModel)
            .where(WorkScheduleModel.farm_id == farm_id, WorkScheduleModel.schedule_id == schedule_id)
            .options(selectinload(WorkScheduleModel.shifts))
        )

    def list_schedules(self, farm_id: str, schedule_date: date | None = None):
        query = (
            select(WorkScheduleModel)
            .where(WorkScheduleModel.farm_id == farm_id)
            .options(selectinload(WorkScheduleModel.shifts))
            .order_by(WorkScheduleModel.schedule_date.desc(), WorkScheduleModel.farm_area)
        )
        if schedule_date is not None:
            query = query.where(WorkScheduleModel.schedule_date == schedule_date)
        return list(self.db.scalars(query).unique())

    def create_schedule(self, farm_id: str, schedule_id: str, schedule_date, farm_area: str):
        schedule = WorkScheduleModel(
            schedule_id=schedule_id,
            farm_id=farm_id,
            schedule_date=schedule_date,
            farm_area=farm_area,
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def get_shift(self, farm_id: str, shift_id: str):
        return self.db.scalar(
            select(WorkShiftModel)
            .join(WorkScheduleModel)
            .where(WorkScheduleModel.farm_id == farm_id, WorkShiftModel.shift_id == shift_id)
        )

    def add_shift(self, schedule: WorkScheduleModel, **values):
        shift = WorkShiftModel(schedule_id=schedule.schedule_id, **values)
        schedule.shifts.append(shift)
        self.db.commit()
        self.db.refresh(shift)
        return shift

    def update_shift(self, shift: WorkShiftModel, **values):
        for key, value in values.items():
            setattr(shift, key, value)
        if shift.status == "COMPLETED":
            shift.completed = True
        elif shift.status in {"TODO", "IN_PROGRESS"}:
            shift.completed = False
        self.db.commit()
        self.db.refresh(shift)
        return shift

    def list_operational_shifts(self, farm_id: str, status: str | None = None):
        query = select(OperationalShiftModel).where(OperationalShiftModel.farm_id == farm_id).order_by(
            OperationalShiftModel.started_at.desc()
        )
        if status:
            query = query.where(OperationalShiftModel.status == status)
        return list(self.db.scalars(query))

    def get_operational_shift(self, farm_id: str, shift_id: str):
        return self.db.scalar(
            select(OperationalShiftModel).where(
                OperationalShiftModel.farm_id == farm_id,
                OperationalShiftModel.shift_id == shift_id,
            )
        )

    def create_operational_shift(self, farm_id: str, **values):
        shift = OperationalShiftModel(farm_id=farm_id, **values)
        self.db.add(shift)
        self.db.commit()
        self.db.refresh(shift)
        return shift

    def close_operational_shift(self, shift: OperationalShiftModel, transferred_actions: int):
        from datetime import datetime, timezone

        shift.status = "closed"
        shift.transferred_actions = transferred_actions
        shift.closed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(shift)
        return shift
