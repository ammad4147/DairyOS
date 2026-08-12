from datetime import date, datetime, time, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dairyos.data.database.base import Base


class WorkScheduleModel(Base):
    __tablename__ = "work_schedules"

    schedule_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    schedule_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    farm_area: Mapped[str] = mapped_column(String(100), nullable=False)
    shifts: Mapped[list["WorkShiftModel"]] = relationship(
        back_populates="schedule",
        cascade="all, delete-orphan",
        order_by="WorkShiftModel.start_time",
    )


class WorkShiftModel(Base):
    __tablename__ = "work_shifts"

    shift_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    schedule_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("work_schedules.schedule_id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    assigned_role: Mapped[str] = mapped_column(String(50), nullable=False)
    assigned_worker_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    task_category: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="TODO")
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    schedule: Mapped[WorkScheduleModel] = relationship(back_populates="shifts")


class OperationalShiftModel(Base):
    __tablename__ = "operational_shifts"

    shift_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    farm_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    shift_name: Mapped[str] = mapped_column(String(200), nullable=False)
    supervisor: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transferred_actions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
