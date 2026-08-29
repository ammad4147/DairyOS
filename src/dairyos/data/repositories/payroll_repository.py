from __future__ import annotations

from datetime import date
from decimal import Decimal

from ..models.payroll import PayrollRecord


class PayrollRepository:
    """Persistence boundary for Finance-owned payroll records."""

    def __init__(self, session=None):
        self.session = session
        self.records: list[PayrollRecord] = []

    def add(self, record: PayrollRecord):
        if self.session:
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
            return record
        self.records.append(record)
        return record

    def get_all(self):
        if self.session:
            return self.session.query(PayrollRecord).order_by(PayrollRecord.period_start.desc(), PayrollRecord.id.desc()).all()
        return list(reversed(self.records))

    def get_by_id(self, record_id: int):
        if self.session:
            return self.session.query(PayrollRecord).filter(PayrollRecord.id == record_id).first()
        return next((item for item in self.records if item.id == record_id), None)

    def get_by_period(self, period_start: date, period_end: date):
        if self.session:
            return self.session.query(PayrollRecord).filter(
                PayrollRecord.period_start == period_start,
                PayrollRecord.period_end == period_end,
            ).order_by(PayrollRecord.id.desc()).all()
        return [
            item for item in self.records
            if item.period_start == period_start and item.period_end == period_end
        ]

    def save(self, record: PayrollRecord):
        if self.session:
            record.updated_at = __import__('dairyos.core.time_utils', fromlist=['utcnow']).utcnow()
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
        return record

    def count(self):
        if self.session:
            return self.session.query(PayrollRecord).count()
        return len(self.records)

    @staticmethod
    def totals(records):
        records = list(records)
        return {
            "record_count": len(records),
            "gross_pay": sum((Decimal(r.gross_pay) for r in records), Decimal("0")),
            "net_pay": sum((Decimal(r.net_pay) for r in records), Decimal("0")),
            "advances": sum((Decimal(r.advances or 0) for r in records), Decimal("0")),
            "deductions": sum((Decimal(r.deductions or 0) for r in records), Decimal("0")),
        }
