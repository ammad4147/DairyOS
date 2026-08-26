from datetime import date as date_type, datetime as datetime_type

from sqlalchemy import func

from ..models.milk_production import MilkProduction
from ..models.animal import Animal
from ..models.treatment_record import TreatmentRecord
from dairyos.core.time_utils import utcnow


INACTIVE_LIFECYCLE_STATUSES = {"DECEASED", "SOLD", "CULLED"}
MILK_YIELD_FIELDS = ("morning_yield", "afternoon_yield", "evening_yield")


class MilkProductionRepository:

    def __init__(self, session=None, animal_repository=None):
        self.session = session
        self.animal_repository = animal_repository
        self.records = []

    def _ensure_animal_exists(self, animal_id):
        """Enforce animal identity, lifecycle, and milk-yield integrity."""
        if not animal_id or not str(animal_id).strip():
            raise ValueError("Milk production requires a permanent animal_id.")

        for field in MILK_YIELD_FIELDS:
            # Repository is a defense-in-depth boundary for non-HTTP callers.
            # A missing value is valid; a numeric negative value is not.
            value = getattr(self, "_pending_production", None)
            if value is not None:
                candidate = getattr(value, field, None)
                if candidate is not None and float(candidate) < 0:
                    raise ValueError(
                        f"Milk production rejected: {field} must be greater than or equal to zero."
                    )

        animal = None
        if self.animal_repository is not None:
            getter = getattr(self.animal_repository, "get_by_animal_id", None)
            if getter is not None:
                animal = getter(str(animal_id))
            exists = animal is not None if animal is not None else self.animal_repository.exists(str(animal_id))
        elif self.session:
            animal = (
                self.session.query(Animal)
                .filter(Animal.animal_id == str(animal_id))
                .first()
            )
            exists = animal is not None
        else:
            exists = True

        if not exists:
            raise ValueError(
                f"Milk production rejected: animal_id '{animal_id}' does not exist."
            )

        if animal is not None:
            lifecycle_status = str(
                getattr(animal, "lifecycle_status", "") or ""
            ).strip().upper()
            active = bool(getattr(animal, "active", True))
            if not active or lifecycle_status in INACTIVE_LIFECYCLE_STATUSES:
                state = lifecycle_status or "INACTIVE"
                raise ValueError(
                    f"Milk production rejected: animal_id '{animal_id}' is {state} and cannot accept production."
                )

    def _validate_production_payload(self, production):
        self._pending_production = production
        try:
            for field in MILK_YIELD_FIELDS:
                value = getattr(production, field, None)
                if value is not None and float(value) < 0:
                    raise ValueError(
                        f"Milk production rejected: {field} must be greater than or equal to zero."
                    )
            self._ensure_animal_exists(production.animal_id)
        finally:
            self._pending_production = None

    def _has_active_withdrawal(self, animal_id, production_at=None) -> bool:
        """Return whether milk is under an active veterinary withdrawal.

        The persisted treatment record is the durable source of truth. The
        in-memory WithdrawalService is an operational cache, not the safety
        authority for a persisted production record.
        """
        if not self.session:
            return False

        check_at = production_at or utcnow()
        treatments = (
            self.session.query(TreatmentRecord)
            .filter(TreatmentRecord.animal_id == str(animal_id))
            .all()
        )

        for treatment in treatments:
            start = treatment.treated_at
            end = treatment.milk_withdrawal_until
            if start is None or end is None:
                continue

            if start.tzinfo is None and check_at.tzinfo is not None:
                start = start.replace(tzinfo=check_at.tzinfo)
            if end.tzinfo is None and check_at.tzinfo is not None:
                end = end.replace(tzinfo=check_at.tzinfo)
            if check_at.tzinfo is None and start.tzinfo is not None:
                start = start.replace(tzinfo=None)
            if check_at.tzinfo is None and end.tzinfo is not None:
                end = end.replace(tzinfo=None)

            if start <= check_at < end:
                return True

        return False

    def _apply_veterinary_status(self, production):
        production_at = getattr(production, "production_date", None) or utcnow()
        if self._has_active_withdrawal(
            production.animal_id,
            production_at,
        ):
            production.status = "WITHDRAWAL"
        elif str(getattr(production, "status", "") or "").upper() == "WITHDRAWAL":
            production.status = "RECORDED"
        return production

    def add(self, production):
        self._validate_production_payload(production)
        self._apply_veterinary_status(production)

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
        """The governed row holding this animal's sessions for one day."""
        production_day = _as_date(production_day)
        if production_day is None:
            return None

        if self.session:
            return (
                self.session.query(MilkProduction)
                .filter(
                    MilkProduction.animal_id == str(animal_id),
                    MilkProduction.session_ledger.is_(True),
                    func.date(MilkProduction.production_date) == production_day,
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
        """Merge a governed session entry into that animal's day row."""
        self._validate_production_payload(production)
        self._apply_veterinary_status(production)

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
                if float(value) < 0:
                    raise ValueError(
                        f"Milk production rejected: {field} must be greater than or equal to zero."
                    )
                setattr(existing, field, value)

        existing.milking_session = production.milking_session
        existing.recorded_at = utcnow()
        existing.calculate_total()

        # Preserve an active withdrawal across all sessions for the day.
        self._apply_veterinary_status(existing)

        if self.session:
            self.session.commit()
            self.session.refresh(existing)

        return existing

    def get_all(self):
        if self.session:
            return self.session.query(MilkProduction).all()
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
            return self.session.query(MilkProduction).count()
        return len(self.records)


def _as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime_type):
        return value.date()
    if isinstance(value, date_type):
        return value
    return date_type.fromisoformat(str(value)[:10])
