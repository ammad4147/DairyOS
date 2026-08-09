from ..models.milk_production import MilkProduction


class MilkProductionRepository:


    def __init__(self, session=None):

        self.session = session
        self.records = []


    def add(self, production):

        if self.session:
            self.session.add(production)
            self.session.commit()
            self.session.refresh(production)
            return production

        self.records.append(production)
        return production


    def get_all(self):

        if self.session:
            return self.session.query(
                MilkProduction
            ).all()

        return self.records


    def get_by_id(self, record_id):

        if self.session:
            return (
                self.session.query(MilkProduction)
                .filter(MilkProduction.id == record_id)
                .first()
            )

        for item in self.records:
            if getattr(item, "id", None) == record_id:
                return item

        return None


    def exists(self, record_id):

        return self.get_by_id(record_id) is not None


    def delete(self, record_id):

        if self.session:

            entity = self.get_by_id(record_id)

            if entity is None:
                return False

            self.session.delete(entity)
            self.session.commit()
            return True

        entity = self.get_by_id(record_id)

        if entity is None:
            return False

        self.records.remove(entity)
        return True


    def count(self):

        if self.session:
            return (
                self.session.query(
                    MilkProduction
                ).count()
            )

        return len(self.records)
