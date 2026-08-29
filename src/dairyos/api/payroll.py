from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dairyos.api.dependencies import get_container
from dairyos.data.models.payroll import PayrollRecord


router = APIRouter(prefix="/farm/payroll", tags=["Finance Payroll"])


class PayrollCreateRequest(BaseModel):
    employee_name: str = Field(min_length=1)
    employee_role: str = Field(min_length=1)
    period_start: date
    period_end: date
    worked_days: Decimal = Field(default=Decimal("0"), ge=0)
    base_pay: Decimal = Field(default=Decimal("0"), ge=0)
    overtime_hours: Decimal = Field(default=Decimal("0"), ge=0)
    overtime_rate: Decimal = Field(default=Decimal("0"), ge=0)
    allowances: Decimal = Field(default=Decimal("0"), ge=0)
    advances: Decimal = Field(default=Decimal("0"), ge=0)
    deductions: Decimal = Field(default=Decimal("0"), ge=0)
    notes: str | None = None


def _repo(container):
    return container.repository_factory.payroll()


def _serialize(record: PayrollRecord) -> dict:
    return {
        "id": record.id,
        "employee_name": record.employee_name,
        "employee_role": record.employee_role,
        "period_start": record.period_start.isoformat(),
        "period_end": record.period_end.isoformat(),
        "worked_days": str(record.worked_days),
        "base_pay": str(record.base_pay),
        "overtime_hours": str(record.overtime_hours),
        "overtime_rate": str(record.overtime_rate),
        "overtime_pay": str(record.overtime_pay),
        "allowances": str(record.allowances),
        "advances": str(record.advances),
        "deductions": str(record.deductions),
        "gross_pay": str(record.gross_pay),
        "net_pay": str(record.net_pay),
        "status": record.status,
        "payment_date": record.payment_date.isoformat() if record.payment_date else None,
        "notes": record.notes,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


@router.get("")
def list_payroll(container=Depends(get_container)):
    records = _repo(container).get_all()
    totals = _repo(container).totals(records)
    return {
        "records": [_serialize(record) for record in records],
        "totals": {key: str(value) if isinstance(value, Decimal) else value for key, value in totals.items()},
    }


@router.post("", status_code=201)
def create_payroll(request: PayrollCreateRequest, container=Depends(get_container)):
    if request.period_end < request.period_start:
        raise HTTPException(status_code=422, detail="period_end must be on or after period_start")
    record = PayrollRecord(**request.model_dump())
    created = _repo(container).add(record)
    return _serialize(created)


@router.post("/{record_id}/pay")
def pay_payroll(record_id: int, payment_date: date | None = None, container=Depends(get_container)):
    record = _repo(container).get_by_id(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    if record.status == "PAID":
        return _serialize(record)
    record.mark_paid(payment_date)
    return _serialize(_repo(container).save(record))
