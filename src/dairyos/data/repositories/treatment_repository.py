from ..models.treatment_record import TreatmentRecord


class TreatmentRepository:

    def __init__(self, session=None):

        self.session = session
        self.records = []

    def add(self, record):

        if self.session:
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
            return record

        self.records.append(record)
        return record

    def get_all(self):

        if self.session:
            return (
                self.session.query(TreatmentRecord)
                .order_by(TreatmentRecord.treated_at.desc())
                .all()
            )

        return self.records

    def get_by_animal(self, animal_id):

        animal_id = str(animal_id)

        if self.session:
            return (
                self.session.query(TreatmentRecord)
                .filter(TreatmentRecord.animal_id == animal_id)
                .order_by(TreatmentRecord.treated_at.desc())
                .all()
            )

        return [
            item
            for item in self.records
            if str(item.animal_id) == animal_id
        ]

    def get_by_id(self, record_id):

        if self.session:
            return (
                self.session.query(TreatmentRecord)
                .filter(TreatmentRecord.id == record_id)
                .first()
            )

        for item in self.records:
            if getattr(item, "id", None) == record_id:
                return item

        return None

    def count(self):

        if self.session:
            return self.session.query(TreatmentRecord).count()

        return len(self.records)
