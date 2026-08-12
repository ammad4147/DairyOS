from ..models.milk_production import MilkProduction
from ..models.animal import Animal


class MilkProductionRepository:


    def __init__(self, session=None, animal_repository=None):

        self.session = session
        self.animal_repository = animal_repository
        self.records = []


    def _ensure_animal_exists(self, animal_id):
        """Enforce the permanent Animal identity invariant for milk records."""
        if not animal_id or not str(animal_id).strip():
            raise ValueError("Milk production requires a permanent animal_id.")

        if self.animal_repository is not None:
            exists = self.animal_repository.exists(str(animal_id))
        elif self.session:
            exists = (
                self.session.query(Animal)
                .filter(Animal.animal_id == str(animal_id))
                .first()
                is not None
            )
        else:
            exists = True

        if not exists:
            raise ValueError(
                f"Milk production rejected: animal_id '{animal_id}' does not exist."
            )


    def add(self, production):

        self._ensure_animal_exists(production.animal_id)

        if self.session:
            self.session.add(production)
            self.session.commit()
            self.session.refresh(production)
            return production

        self.records.append(production)
        return production


    def save(self, production):
        """Compatibility persistence contract used by farm data entry."""
        return self.add(production)


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


    def get_by_animal_id(self, animal_id):
        """Return persistent milk records belonging to one permanent Animal ID."""
        if not animal_id:
            return []

        if self.session:
            return (
                self.session.query(MilkProduction)
                .filter(MilkProduction.animal_id == str(animal_id))
                .order_by(MilkProduction.production_date.asc())
                .all()
            )

        return [
            item for item in self.records
            if item.animal_id == str(animal_id)
        ]


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
