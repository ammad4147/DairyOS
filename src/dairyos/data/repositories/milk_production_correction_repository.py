from __future__ import annotations

from ..models.milk_production_correction import MilkProductionCorrection


class MilkProductionCorrectionRepository:
    """Read/insert boundary for Milk correction history."""

    def __init__(self, session=None):
        self.session = session
        self.records = []

    def add(self, record: MilkProductionCorrection):
        if self.session is None:
            self.records.append(record)
            return record

        self.session.add(record)
        if not self.session.info.get("operational_write_managed", False):
            self.session.commit()
            self.session.refresh(record)
        return record

    def get_for_production(self, production_id: int):
        if self.session is None:
            return [
                row
                for row in self.records
                if row.production_id == production_id
            ]

        return (
            self.session.query(MilkProductionCorrection)
            .filter(MilkProductionCorrection.production_id == production_id)
            .order_by(MilkProductionCorrection.corrected_at.asc(), MilkProductionCorrection.id.asc())
            .all()
        )
