from datetime import date as date_type, datetime as datetime_type

from sqlalchemy import func

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


    def ledger_row_for_animal_day(self, animal_id, production_day):
        """The governed row holding this animal's sessions for one day.

        Only ledger rows are considered. Pre-ledger history genuinely contains
        duplicate animal-days, so matching against it would merge records that
        were never meant to be one.
        """

        production_day = _as_date(production_day)

        if production_day is None:
            return None

        if self.session:
            return (
                self.session.query(MilkProduction)
                .filter(
                    MilkProduction.animal_id == str(animal_id),
                    MilkProduction.session_ledger.is_(True),
                    func.date(MilkProduction.production_date)
                    == production_day,
                )
                .first()
            )

        for item in self.records:
            if (
                str(item.animal_id) == str(animal_id)
                and bool(getattr(item, "session_ledger", False))
                and _as_date(item.production_date) == production_day
            ):
                return item

        return None


    def upsert_ledger_day(self, production):
        """Merge a governed session entry into that animal's day row.

        One animal-day is one row with a slot per session: the morning entry
        opens it, the evening entry fills the remaining slot. Inserting a
        second row per session instead would make "how much did she give
        today" a question about grouping rather than a lookup, and is what the
        partial unique index exists to prevent.

        Only supplied (non-None) yields are merged, so writing the evening
        figure never overwrites the morning one with a null.
        """

        self._ensure_animal_exists(production.animal_id)

        existing = self.ledger_row_for_animal_day(
            production.animal_id,
            production.production_date,
        )

        if existing is None:
            production.calculate_total()
            return self.add(production)

        for field in (
            "morning_yield",
            "afternoon_yield",
            "evening_yield",
        ):
            value = getattr(production, field, None)
            if value is not None:
                setattr(existing, field, value)

        existing.milking_session = production.milking_session
        existing.recorded_at = datetime_type.utcnow()

        # A withdrawal hold on any session withholds the animal-day. Losing
        # that on the next session's entry would put withheld milk back into
        # the saleable total.
        if str(production.status) == "WITHHELD":
            existing.status = "WITHHELD"

        existing.calculate_total()

        if self.session:
            self.session.commit()
            self.session.refresh(existing)

        return existing


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


def _as_date(value):
    if value is None:
        return None

    if isinstance(value, datetime_type):
        return value.date()

    if isinstance(value, date_type):
        return value

    return date_type.fromisoformat(str(value)[:10])
