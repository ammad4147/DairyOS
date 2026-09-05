from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dairyos.api.dependencies import get_container
from dairyos.core.time_utils import utcnow
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.payroll import PayrollRecord
from dairyos.data.repositories.repository_factory import RepositoryFactory

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


def _payroll_subcategory(role: str) -> str:
    normalized = role.strip().lower()
    if "milker" in normalized:
        return "Milker Wages"
    if "feed" in normalized or "feeder" in normalized:
        return "Feeder / Shed Worker Wages"
    if "manager" in normalized or "supervisor" in normalized:
        return "Supervisor / Farm Manager Salary"
    return "Daily / Temporary Labor"


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
        "finance_transaction_id": record.finance_transaction_id,
        "notes": record.notes,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


@router.get("")
def list_payroll(container=Depends(get_container)):
    repo = _repo(container)
    records = repo.get_all()
    totals = repo.totals(records)
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
    runtime_factory = container.repository_factory

    # Preserve non-persistent test/compatibility factories where applicable.
    if getattr(runtime_factory, "session", None) is None:
        return _pay_payroll(
            record_id,
            payment_date,
            runtime_factory,
        )

    # Payroll payment and Finance posting are one business action and therefore
    # receive one isolated application transaction.
    factory = RepositoryFactory.create()
    try:
        with factory.session.begin():
            return _pay_payroll(
                record_id,
                payment_date,
                factory,
            )
    finally:
        factory.close()


def _pay_payroll(record_id, payment_date, factory):
    repo = factory.payroll()
    session = getattr(factory, "session", None)

    # A payroll payment and its Finance posting are one business action.  The
    # persistent path takes a row lock and performs a single commit so a
    # failed Finance write cannot leave Payroll marked PAID (or vice versa).
    if session is not None:
        record = (
            session.query(PayrollRecord)
            .filter(PayrollRecord.id == record_id)
            .with_for_update()
            .first()
        )
    else:
        record = repo.get_by_id(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    if record.status == "PAID" and record.finance_transaction_id is not None:
        return _serialize(record)

    finance_repo = factory.finance()
    source_reference = f"PAYROLL#{record.id}"
    existing = next(
        (
            row
            for row in finance_repo.get_all()
            if str(row.reference or "") == source_reference
            and str(row.status or "").upper() != "VOID"
        ),
        None,
    )
    if existing is not None:
        record.finance_transaction_id = existing.id
        record.status = "PAID"
        record.payment_date = payment_date or existing.settled_date or utcnow().date()
        if session is not None:
            try:
                session.add(record)
                session.flush()
                session.refresh(record)
            except Exception:
                session.rollback()
                raise
        else:
            repo.save(record)
        return _serialize(record)

    pay_date = payment_date or utcnow().date()
    quantity = float(record.worked_days or 0)
    net_pay = Decimal(record.net_pay)
    transaction = FinancialTransaction(
        transaction_type="EXPENSE",
        category="LABOUR",
        amount=net_pay,
        transaction_date=datetime.combine(pay_date, time.min),
        reference=source_reference,
        payment_method="BANK",
        counterparty=record.employee_name,
        notes=f"Payroll payment for {record.employee_role}; period {record.period_start.isoformat()} to {record.period_end.isoformat()}.",
        currency="PKR",
        status="PAID",
        master_category="OPEX",
        sub_category=_payroll_subcategory(record.employee_role),
        custom_specification=record.employee_role,
        quantity=quantity if quantity > 0 else None,
        unit="day" if quantity > 0 else None,
        unit_rate=net_pay / Decimal(str(quantity)) if quantity > 0 else None,
        settled_date=pay_date,
        payroll_record_id=record.id,
    )
    if session is not None:
        try:
            session.add(transaction)
            session.flush()
            record.mark_paid(pay_date)
            record.finance_transaction_id = transaction.id
            session.add(record)
            session.flush()
            session.refresh(record)
        except Exception:
            session.rollback()
            raise
    else:
        saved = finance_repo.add(transaction)
        record.mark_paid(pay_date)
        record.finance_transaction_id = saved.id
        repo.save(record)
    return _serialize(record)
