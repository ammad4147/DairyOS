from __future__ import annotations

from datetime import date, datetime, time, timezone

from dairyos.data.models.milk_disposition import MilkDisposition


AUTO_WASTAGE_PREFIX = "AUTO_WITHDRAWAL_WASTAGE"


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def animal_withdrawn_on_date(withdrawal_service, animal_id: str, day: date) -> bool:
    """Return whether any treatment-withdrawal period overlaps ``day``."""

    if withdrawal_service is None:
        return False

    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = datetime.combine(day, time.max, tzinfo=timezone.utc)

    getter = getattr(withdrawal_service, "get_periods_for_animal", None)
    if callable(getter):
        for period in getter(str(animal_id)):
            period_start = _aware_utc(period.start_time)
            period_end = _aware_utc(period.end_time)
            if period_start <= end and period_end >= start:
                return True
        return False

    checker = getattr(withdrawal_service, "is_animal_withdrawn", None)
    if callable(checker):
        return bool(checker(str(animal_id), at=end))

    return False


def ensure_withdrawal_wastage(
    *,
    repository_factory,
    withdrawal_service,
    animal_id: str,
    production_date: date,
    milking_session: str,
    quantity_litres: float,
    recorded_by: str,
):
    """Persist one idempotent WASTAGE disposition for withdrawn milk.

    The milk itself remains ordinary recorded biological production. This
    paired disposition is the physical reconciliation fact that makes those
    litres unavailable to sale while retaining the animal's true production
    history.
    """

    litres = float(quantity_litres or 0.0)
    if litres <= 0:
        return None

    if not animal_withdrawn_on_date(
        withdrawal_service,
        str(animal_id),
        production_date,
    ):
        return None

    marker = (
        f"{AUTO_WASTAGE_PREFIX}:"
        f"{animal_id}:{production_date.isoformat()}:"
        f"{str(milking_session).upper()}"
    )

    repo = repository_factory.milk_dispositions()
    for existing in repo.get_by_date(production_date) or []:
        if (
            marker in str(getattr(existing, "notes", "") or "")
            and str(getattr(existing, "status", "RECORDED") or "RECORDED").upper()
            != "VOID"
        ):
            return existing

    item = MilkDisposition(
        production_date=production_date,
        disposition_type="WASTAGE",
        quantity_litres=litres,
        amount_due=0.0,
        amount_received=0.0,
        notes=(
            f"{marker} | Automatically recorded because animal {animal_id} "
            "was under an active milk-withdrawal period. Milk retained in "
            "production history and excluded from sale."
        ),
        recorded_by=recorded_by,
        status="RECORDED",
    )
    return repo.add(item)
