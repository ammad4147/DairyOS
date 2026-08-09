from datetime import datetime

from ..models.animal import Animal
from ..models.animal_milking_schedule_history import (
    AnimalMilkingScheduleHistory,
)


class AnimalRepository:
    """
    Operational livestock repository.

    Real, database-backed implementation. Method names and behavior
    preserved from the original in-memory version for compatibility;
    the original docstring anticipated this upgrade ("persistence
    integration can be introduced later without changing service
    contracts") — this fulfills that.
    """

    def __init__(self, session=None):

        self.session = session
        self.records = []

    def add(self, animal):

        if self.session:
            self.session.add(animal)
            self.session.commit()
            self.session.refresh(animal)
            return animal

        self.records.append(animal)
        return animal

 
    def save(
        self,
        animal,
    ):
        """
        Compatibility persistence contract.

        Existing application services use save().
        Database implementation internally uses add().
        """

        return self.add(
            animal
        )



    def get_all(self):

        if self.session:
            return self.session.query(Animal).all()

        return self.records

    
    def count(self):

        if self.session:
            return self.session.query(Animal).count()

        return len(self.records)

    def get_by_animal_id(self, animal_id):

        if self.session:
            return (
                self.session.query(Animal)
                .filter(Animal.animal_id == animal_id)
                .first()
            )

        for animal in self.records:
            if animal.animal_id == animal_id:
                return animal

        return None

    def exists(self, animal_id):

        return self.get_by_animal_id(animal_id) is not None

    def find_by_status(self, status):

        if self.session:
            return (
                self.session.query(Animal)
                .filter(Animal.status == status)
                .all()
            )

        return [a for a in self.records if a.status == status]

    def find_by_lifecycle_status(self, lifecycle_status):

        if self.session:
            return (
                self.session.query(Animal)
                .filter(Animal.lifecycle_status == lifecycle_status)
                .all()
            )

        return [
            a for a in self.records
            if a.lifecycle_status == lifecycle_status
        ]

    def find_by_location(self, location):

        if self.session:
            return (
                self.session.query(Animal)
                .filter(Animal.location == location)
                .all()
            )

        return [a for a in self.records if a.location == location]

    def find_by_group(self, production_group):

        if self.session:
            return (
                self.session.query(Animal)
                .filter(Animal.production_group == production_group)
                .all()
            )

        return [
            a for a in self.records
            if a.production_group == production_group
        ]

    def active_animals(self):

        if self.session:
            return (
                self.session.query(Animal)
                .filter(Animal.active.is_(True))
                .all()
            )

        return [a for a in self.records if a.active]

    def inactive_animals(self):

        if self.session:
            return (
                self.session.query(Animal)
                .filter(Animal.active.is_(False))
                .all()
            )

        return [a for a in self.records if not a.active]

    def currently_milking_animals(self):
        """
        Animals eligible for milk-session scheduling — the population
        the measurement-schedule engine generates PENDING sessions for.
        """

        if self.session:
            return (
                self.session.query(Animal)
                .filter(Animal.is_currently_milking.is_(True))
                .filter(Animal.active.is_(True))
                .all()
            )

        return [
            a for a in self.records
            if a.is_currently_milking and a.active
        ]

    def set_milking_frequency(
        self,
        animal_id,
        new_frequency,
        changed_by=None,
        reason=None,
    ):
        """
        Changes an animal's milking frequency, closing out the
        previous history record and opening a new one — preserving
        full traceability of frequency changes over the animal's
        lifecycle, per the confirmed design.
        """

        if not self.session:
            raise RuntimeError(
                "set_milking_frequency requires a database session"
            )

        animal = self.get_by_animal_id(animal_id)

        if animal is None:
            return None

        now = datetime.utcnow()

        current_history = (
            self.session.query(AnimalMilkingScheduleHistory)
            .filter(
                AnimalMilkingScheduleHistory.animal_id == animal_id,
                AnimalMilkingScheduleHistory.effective_to.is_(None),
            )
            .first()
        )

        if current_history:
            current_history.effective_to = now

        new_history = AnimalMilkingScheduleHistory(
            animal_id=animal_id,
            milking_frequency=new_frequency,
            effective_from=now,
            changed_by=changed_by,
            reason=reason,
        )
        self.session.add(new_history)

        animal.milking_frequency = new_frequency
        animal.updated_at = now

        self.session.commit()
        self.session.refresh(animal)

        return animal

    def get_milking_frequency_history(self, animal_id):

        if not self.session:
            return []

        return (
            self.session.query(AnimalMilkingScheduleHistory)
            .filter(AnimalMilkingScheduleHistory.animal_id == animal_id)
            .order_by(AnimalMilkingScheduleHistory.effective_from.desc())
            .all()
        )
