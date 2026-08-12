from datetime import date, datetime, time, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from dairyos.api.auth import get_current_user, require_roles
from dairyos.application.identity.models.authorization_role import AuthorizationRole
from dairyos.data.database.models.user_account_model import UserAccountModel
from dairyos.data.database.session import get_session
from dairyos.operations.repositories.workforce_repository import SqlAlchemyWorkforceRepository


router = APIRouter(prefix="/farm/workforce", tags=["Workforce"])
MANAGERS = (AuthorizationRole.OWNER, AuthorizationRole.MANAGER)


class ScheduleCreateRequest(BaseModel):
    schedule_date: date
    farm_area: str = Field(min_length=1, max_length=100)
    schedule_id: str | None = None


class TaskCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    start_time: time
    end_time: time
    assigned_role: str = Field(min_length=1, max_length=50)
    assigned_worker_id: str | None = None
    task_category: str = Field(min_length=1, max_length=100)


class TaskUpdateRequest(BaseModel):
    status: str = Field(pattern="^(TODO|IN_PROGRESS|COMPLETED)$")


class OperationalShiftCreateRequest(BaseModel):
    shift_name: str = Field(min_length=1, max_length=200)


class OperationalShiftCloseRequest(BaseModel):
    transferred_actions: int = Field(default=0, ge=0)


def _serialize_schedule(schedule):
    return {
        "schedule_id": schedule.schedule_id,
        "schedule_date": schedule.schedule_date,
        "farm_area": schedule.farm_area,
        "completion_percentage": (
            round(sum(1 for s in schedule.shifts if s.completed) / len(schedule.shifts) * 100, 2)
            if schedule.shifts else 0.0
        ),
        "total_tasks": len(schedule.shifts),
        "completed_tasks": sum(1 for s in schedule.shifts if s.completed),
        "shifts": [_serialize_task(s) for s in schedule.shifts],
    }


def _serialize_task(task):
    return {
        "shift_id": task.shift_id,
        "schedule_id": task.schedule_id,
        "name": task.name,
        "start_time": task.start_time,
        "end_time": task.end_time,
        "assigned_role": task.assigned_role,
        "assigned_worker_id": task.assigned_worker_id,
        "task_category": task.task_category,
        "status": task.status,
        "completed": task.completed,
    }


def _serialize_operational_shift(shift):
    return {
        "shift_id": shift.shift_id,
        "shift_name": shift.shift_name,
        "supervisor": shift.supervisor,
        "status": shift.status,
        "started_at": shift.started_at,
        "closed_at": shift.closed_at,
        "transferred_actions": shift.transferred_actions,
    }


def _same_farm_worker(db: Session, farm_id: str, worker_id: str) -> bool:
    return db.scalar(
        select(UserAccountModel.user_id).where(
            UserAccountModel.user_id == worker_id,
            UserAccountModel.farm_id == farm_id,
            UserAccountModel.active.is_(True),
        )
    ) is not None


@router.get("/schedules")
def list_schedules(
    schedule_date: date | None = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    return [_serialize_schedule(s) for s in SqlAlchemyWorkforceRepository(db).list_schedules(current_user["farm_id"], schedule_date)]


@router.post("/schedules", status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreateRequest,
    current_user: dict = Depends(require_roles(*MANAGERS)),
    db: Session = Depends(get_session),
):
    repo = SqlAlchemyWorkforceRepository(db)
    schedule = repo.create_schedule(
        farm_id=current_user["farm_id"],
        schedule_id=payload.schedule_id or str(uuid4()),
        schedule_date=payload.schedule_date,
        farm_area=payload.farm_area,
    )
    return _serialize_schedule(schedule)


@router.post("/schedules/{schedule_id}/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    schedule_id: str,
    payload: TaskCreateRequest,
    current_user: dict = Depends(require_roles(*MANAGERS)),
    db: Session = Depends(get_session),
):
    repo = SqlAlchemyWorkforceRepository(db)
    schedule = repo.get_schedule(current_user["farm_id"], schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if payload.assigned_worker_id and not _same_farm_worker(db, current_user["farm_id"], payload.assigned_worker_id):
        raise HTTPException(status_code=400, detail="Assigned worker is not an active user in this farm")
    task = repo.add_shift(schedule, shift_id=str(uuid4()), **payload.model_dump())
    return _serialize_task(task)


@router.patch("/tasks/{shift_id}")
def update_task(
    shift_id: str,
    payload: TaskUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    repo = SqlAlchemyWorkforceRepository(db)
    task = repo.get_shift(current_user["farm_id"], shift_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user["role"] not in {role.value for role in MANAGERS} and task.assigned_worker_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Only the assigned worker or a manager can update this task")
    return _serialize_task(repo.update_shift(task, status=payload.status))


@router.get("/operational-shifts")
def list_operational_shifts(
    status_filter: str | None = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    return [_serialize_operational_shift(s) for s in SqlAlchemyWorkforceRepository(db).list_operational_shifts(current_user["farm_id"], status_filter)]


@router.post("/operational-shifts", status_code=status.HTTP_201_CREATED)
def create_operational_shift(
    payload: OperationalShiftCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    shift = SqlAlchemyWorkforceRepository(db).create_operational_shift(
        farm_id=current_user["farm_id"],
        shift_name=payload.shift_name,
        supervisor=current_user["sub"],
        status="open",
        started_at=datetime.now(timezone.utc),
    )
    return _serialize_operational_shift(shift)


@router.post("/operational-shifts/{shift_id}/close")
def close_operational_shift(
    shift_id: str,
    payload: OperationalShiftCloseRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    repo = SqlAlchemyWorkforceRepository(db)
    shift = repo.get_operational_shift(current_user["farm_id"], shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Operational shift not found")
    if current_user["role"] not in {role.value for role in MANAGERS} and shift.supervisor != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Only the supervisor or a manager can close this shift")
    return _serialize_operational_shift(repo.close_operational_shift(shift, payload.transferred_actions))


@router.get("/summary")
def workforce_summary(
    schedule_date: date | None = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    schedules = SqlAlchemyWorkforceRepository(db).list_schedules(current_user["farm_id"], schedule_date)
    tasks = [task for schedule in schedules for task in schedule.shifts]
    active_shifts = SqlAlchemyWorkforceRepository(db).list_operational_shifts(current_user["farm_id"], "open")
    present_ids = {task.assigned_worker_id for task in tasks if task.assigned_worker_id and task.status != "COMPLETED"}
    return {
        "staff_present": len(present_ids),
        "on_duty": len(active_shifts),
        "tasks_today": len(tasks),
        "completed": sum(1 for task in tasks if task.status == "COMPLETED"),
        "outstanding": sum(1 for task in tasks if task.status != "COMPLETED"),
        "open_operational_shifts": len(active_shifts),
    }
