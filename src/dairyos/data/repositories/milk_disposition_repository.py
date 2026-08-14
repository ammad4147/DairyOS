from datetime import date

from dairyos.data.models.milk_disposition import MilkDisposition


class MilkDispositionRepository:
    def __init__(self, session=None):
        self.session = session
        self.records = []

    def add(self, disposition):
        if self.session:
            self.session.add(disposition)
            self.session.commit()
            self.session.refresh(disposition)
            return disposition
        self.records.append(disposition)
        return disposition

    save = add

    def get_all(self):
        if self.session:
            return (
                self.session.query(MilkDisposition)
                .order_by(MilkDisposition.production_date.asc(), MilkDisposition.id.asc())
                .all()
            )
        return list(self.records)

    def get_by_date(self, production_date: date):
        if self.session:
            return (
                self.session.query(MilkDisposition)
                .filter(MilkDisposition.production_date == production_date)
                .order_by(MilkDisposition.id.asc())
                .all()
            )
        return [r for r in self.records if r.production_date == production_date]

    def get_by_sale_id(self, sale_id: str):
        if self.session:
            return (
                self.session.query(MilkDisposition)
                .filter(MilkDisposition.sale_id == sale_id)
                .first()
            )
        return next((r for r in self.records if r.sale_id == sale_id), None)

    def count(self):
        if self.session:
            return self.session.query(MilkDisposition).count()
        return len(self.records)
