from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String, Text

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class PayrollRecord(Base):
    """Persisted payroll period record owned by Finance."""

    __tablename__ = "payroll_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_name = Column(String, nullable=False, index=True)
    employee_role = Column(String, nullable=False, index=True)
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    worked_days = Column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    base_pay = Column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    overtime_hours = Column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    overtime_rate = Column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    allowances = Column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    advances = Column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    deductions = Column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    status = Column(String, nullable=False, default="DRAFT", index=True)
    payment_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow)

    @property
    def overtime_pay(self):
        return Decimal(self.overtime_hours or 0) * Decimal(self.overtime_rate or 0)

    @property
    def gross_pay(self):
        return Decimal(self.base_pay or 0) + self.overtime_pay + Decimal(self.allowances or 0)

    @property
    def net_pay(self):
        return self.gross_pay - Decimal(self.advances or 0) - Decimal(self.deductions or 0)

    def mark_paid(self, payment_date: date | None = None):
        self.status = "PAID"
        self.payment_date = payment_date or utcnow().date()
        self.updated_at = datetime.now().astimezone().replace(tzinfo=None)
