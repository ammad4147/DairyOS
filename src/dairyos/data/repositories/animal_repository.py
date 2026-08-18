from datetime import datetime, timezone

from ..models.animal import Animal
from ..models.animal_milking_schedule_history import (
    AnimalMilkingScheduleHistory,
)
from dairyos.core.time_utils import utcnow


class AnimalRepository:
    """
    Operational livestock repository.

    Real, database-backed implementation. Method names and behavior
    preserved from the original in-memory version for compatibility.
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

    def save(self, animal):
        return self.add(animal)

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
            a
            for a in self.records
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
            a
            for a in self.records
            if a.production_group == production_group
        ]

    def find_by_dam(self, dam_id):
        if not dam_id:
            return []

        if self.session:
            return (
                self.session.query(Animal)
                .filter(Animal.dam_id == str(dam_id))
                .all()
            )

        return [
            a
            for a in self.records
            if getattr(a, "dam_id", None) == str(dam_id)
        ]

    def find_by_sire(self, sire_id):
        if not sire_id:
            return []

        if self.session:
            return (
                self.session.query(Animal)
                .filter(Animal.sire_id == str(sire_id))
                .all()
            )

        return [
            a
            for a in self.records
            if getattr(a, "sire_id", None) == str(sire_id)
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
        Animals eligible for milk-session scheduling.
        """
        if self.session:
            return (
                self.session.query(Animal)
                .filter(Animal.is_currently_milking.is_(True))
                .filter(Animal.active.is_(True))
                .all()
            )

        return [
            a
            for a in self.records
            if a.is_currently_milking and a.active
        ]

    @staticmethod
    def _normalize_effective_from(value):
        """
        Convert an API/database effective-date value into the naive UTC
        datetime representation used by the existing DateTime columns.

        Supported inputs:
          - None
          - datetime
          - ISO date string
          - ISO datetime string, including trailing Z
        """
        if value is None:
            return utcnow()

        if isinstance(value, datetime):
            parsed = value
        else:
            text = str(value).strip()
            if not text:
                return utcnow()

            text = text.replace("Z", "+00:00")

            try:
                parsed = datetime.fromisoformat(text)
            except ValueError as exc:
                raise ValueError(
                    "effective_date must be a valid ISO date or datetime"
                ) from exc

        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)

        return parsed

    @staticmethod
    def _is_initial_schedule(record):
        """
        The initial schedule is automatically created when an animal is
        registered. It is a baseline/default fact, not an operator-entered
        schedule change.

        An explicitly-entered historical schedule must be allowed to
        supersede this baseline even when the baseline starts later.
        """
        reason = getattr(record, "reason", None)
        changed_by = getattr(record, "changed_by", None)

        return (
            str(reason or "").strip().lower() == "initial"
            and changed_by in (None, "")
        )

    def set_milking_frequency(
        self,
        animal_id,
        new_frequency,
        changed_by=None,
        reason=None,
        effective_date=None,
    ):
        """
        Change an animal's milking frequency with effective-dated history.

        Semantics:

        * A normal/current change starts at the requested effective time and
          closes the previous explicit schedule.
        * A backdated explicit change remains effective until the next
          explicit schedule change.
        * The automatically-created ``initial`` schedule never truncates a
          later explicit backdated change.
        """
        if not self.session:
            raise RuntimeError(
                "set_milking_frequency requires a database session"
            )

        animal = self.get_by_animal_id(animal_id)

        if animal is None:
            return None

        now = utcnow()
        effective_from = self._normalize_effective_from(
            effective_date
        )

        histories = (
            self.session.query(AnimalMilkingScheduleHistory)
            .filter(
                AnimalMilkingScheduleHistory.animal_id == animal_id
            )
            .order_by(
                AnimalMilkingScheduleHistory.effective_from.asc()
            )
            .all()
        )

        exact_history = next(
            (
                record
                for record in histories
                if (
                    record.effective_from is not None
                    and record.effective_from == effective_from
                )
            ),
            None,
        )

        if exact_history is not None:
            exact_history.milking_frequency = new_frequency
            exact_history.changed_by = changed_by
            exact_history.reason = reason

            animal.milking_frequency = new_frequency
            animal.updated_at = now

            self.session.commit()
            self.session.refresh(animal)

            return animal

        # The next boundary is the first EXPLICIT schedule beginning after
        # the requested date. The automatic "initial" baseline is not such a
        # boundary because it must not truncate a backdated operator change.
        next_history = next(
            (
                record
                for record in histories
                if (
                    record.effective_from is not None
                    and record.effective_from > effective_from
                    and not self._is_initial_schedule(record)
                )
            ),
            None,
        )

        # Find the most recent history before the requested date.
        previous_history = None

        for record in histories:
            if (
                record.effective_from is not None
                and record.effective_from < effective_from
            ):
                previous_history = record
            else:
                break

        # Only close a predecessor if it is genuinely before the new
        # effective date. The initial baseline may begin after the requested
        # date and therefore must not be given an inverted interval.
        if previous_history is not None:
            previous_history.effective_to = effective_from

        new_history = AnimalMilkingScheduleHistory(
            animal_id=animal_id,
            milking_frequency=new_frequency,
            effective_from=effective_from,
            effective_to=(
                next_history.effective_from
                if next_history is not None
                else None
            ),
            changed_by=changed_by,
            reason=reason,
        )
        self.session.add(new_history)

        # For a historical explicit change, do not alter the current Animal
        # fact away from the latest known schedule. This remains the live
        # current value while the history table remains authoritative for
        # date-aware reads.
        latest_explicit = max(
            (
                record
                for record in histories + [new_history]
                if not self._is_initial_schedule(record)
                and record.effective_from is not None
            ),
            key=lambda record: record.effective_from,
            default=None,
        )

        if (
            latest_explicit is not None
            and latest_explicit.effective_from <= now
        ):
            animal.milking_frequency = latest_explicit.milking_frequency
        else:
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
            .filter(
                AnimalMilkingScheduleHistory.animal_id == animal_id
            )
            .order_by(
                AnimalMilkingScheduleHistory.effective_from.desc()
            )
            .all()
        )
