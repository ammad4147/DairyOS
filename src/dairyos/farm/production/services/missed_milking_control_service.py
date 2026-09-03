from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from dairyos.farm.findings.services.operational_finding_service import OperationalFindingService
from dairyos.farm.herd.services.animal_milking_schedule_service import AnimalMilkingScheduleService
from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority

MISSED_DEDUPE_PREFIX = "MILK_MISSED_SESSION"
REJECTION_PREFIX = "MISSED_MILK_REJECTED:"
AUTO_RESOLUTION_NOTE = "MISSED_MILK_LATE_ENTRY_COMPLETED"
OPEN_STATUSES = frozenset({"RAISED", "ACKNOWLEDGED", "REINSTATED"})


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _status(value: Any) -> str:
    return str(value or "").strip().upper()


class MissedMilkingControlService:
    def __init__(self, repository_factory):
        self.factory = repository_factory
        self.animal_repository = repository_factory.animal()
        self.milk_repository = repository_factory.milk()
        self.session_ledger = repository_factory.milking_session_ledger()
        self.finding_repository = repository_factory.operational_findings()
        self.schedule_service = AnimalMilkingScheduleService(repository=self.animal_repository)

    @staticmethod
    def dedupe_key(production_date: date, animal_id: str) -> str:
        return f"{MISSED_DEDUPE_PREFIX}:{production_date.isoformat()}:{animal_id}"

    @staticmethod
    def _dedupe_date(value: str | None) -> date | None:
        text = str(value or "")
        prefix = f"{MISSED_DEDUPE_PREFIX}:"
        if not text.startswith(prefix):
            return None
        parts = text.split(":", 2)
        if len(parts) != 3:
            return None
        try:
            return date.fromisoformat(parts[1])
        except ValueError:
            return None

    @staticmethod
    def _explicitly_rejected(findings) -> bool:
        return any(
            _status(getattr(item, "status", None)) == "RESOLVED"
            and str(getattr(item, "resolution_note", "") or "").startswith(REJECTION_PREFIX)
            for item in findings
        )

    def _scan_bounds(self, *, as_of_date: date | None, lookback_days: int) -> tuple[date | None, date | None]:
        today = as_of_date or OperationalDateAuthority().current_date()
        latest_complete = today - timedelta(days=1)
        days = max(1, min(int(lookback_days), 90))
        start = latest_complete - timedelta(days=days - 1)
        earliest = None
        try:
            earliest = _as_date(self.session_ledger.earliest_date())
        except (AttributeError, TypeError):
            earliest = None
        if earliest is None:
            governed_rows = [
                row for row in (self.milk_repository.get_all() or [])
                if bool(getattr(row, "session_ledger", False))
            ]
            dates = [_as_date(getattr(row, "production_date", None)) for row in governed_rows]
            dates = [item for item in dates if item is not None]
            earliest = min(dates) if dates else None
        if earliest is not None:
            start = max(start, earliest)
        if start > latest_complete:
            return None, None
        return start, latest_complete

    @staticmethod
    def _animal_entry_day(animal, earliest_recorded: date | None) -> date | None:
        created = _as_date(getattr(animal, "created_at", None))
        acquisition = _as_date(getattr(animal, "date_of_acquisition", None))
        if earliest_recorded is not None:
            return min(earliest_recorded, created) if created is not None else earliest_recorded
        return created or acquisition

    @staticmethod
    def _animal_stop_day(animal) -> date | None:
        currently_milking = bool(getattr(animal, "is_currently_milking", False))
        active = bool(getattr(animal, "active", True))
        lifecycle = _status(getattr(animal, "lifecycle_status", None))
        if active and currently_milking and lifecycle not in {"SOLD", "DECEASED"}:
            return None
        return _as_date(getattr(animal, "updated_at", None))

    def _recorded_sessions(self, rows) -> dict[tuple[str, date], set[str]]:
        observed: dict[tuple[str, date], set[str]] = defaultdict(set)
        for row in rows:
            if not bool(getattr(row, "session_ledger", False)):
                continue
            if _status(getattr(row, "status", None)) in {"VOID", "NOT_MILKED", "CANCELLED", "DELETED"}:
                continue
            production_date = _as_date(getattr(row, "production_date", None) or getattr(row, "recorded_at", None))
            animal_id = str(getattr(row, "animal_id", "") or "").strip()
            if production_date is None or not animal_id:
                continue
            values = (
                ("MORNING", getattr(row, "morning_yield", None)),
                ("AFTERNOON", getattr(row, "afternoon_yield", None)),
                ("EVENING", getattr(row, "evening_yield", None)),
            )
            entered_any = False
            for session, value in values:
                if value is not None:
                    observed[(animal_id, production_date)].add(session)
                    entered_any = True
            if not entered_any:
                declared = _status(getattr(row, "milking_session", None))
                total = getattr(row, "total_yield", None)
                if declared and total is not None:
                    observed[(animal_id, production_date)].add(declared)
        return observed

    def _farm_not_milked(self, production_date: date) -> set[str]:
        try:
            rows = self.session_ledger.get_by_date(production_date) or []
        except AttributeError:
            return set()
        return {
            _status(getattr(row, "milking_session", None))
            for row in rows
            if _status(getattr(row, "status", None)) == "NOT_MILKED"
            and _status(getattr(row, "milking_session", None))
        }

    def _scan(self, *, as_of_date: date | None, lookback_days: int) -> dict[str, Any]:
        start, end = self._scan_bounds(as_of_date=as_of_date, lookback_days=lookback_days)
        if start is None or end is None:
            return {"scan_start": None, "scan_end": None, "conditions": []}
        animals = list(self.animal_repository.get_all() or [])
        rows = list(self.milk_repository.get_all() or [])
        observed = self._recorded_sessions(rows)
        earliest_by_animal: dict[str, date] = {}
        for (animal_id, production_date), sessions in observed.items():
            if not sessions:
                continue
            current = earliest_by_animal.get(animal_id)
            if current is None or production_date < current:
                earliest_by_animal[animal_id] = production_date
        histories: dict[str, list[Any]] = {}
        for animal in animals:
            animal_id = str(getattr(animal, "animal_id", "") or "").strip()
            try:
                histories[animal_id] = list(
                    self.animal_repository.get_milking_frequency_history(animal_id) or []
                )
            except AttributeError:
                histories[animal_id] = []
        conditions: list[dict[str, Any]] = []
        current = start
        while current <= end:
            farm_not_milked = self._farm_not_milked(current)
            for animal in animals:
                animal_id = str(getattr(animal, "animal_id", "") or "").strip()
                if not animal_id:
                    continue
                entry_day = self._animal_entry_day(animal, earliest_by_animal.get(animal_id))
                if entry_day is not None and current < entry_day:
                    continue
                stop_day = self._animal_stop_day(animal)
                if stop_day is not None and current >= stop_day:
                    continue
                snapshot = self.schedule_service.get_schedule_snapshot(
                    animal, current, history=histories.get(animal_id, [])
                )
                expected = list(snapshot.expected_sessions)
                if not expected:
                    continue
                recorded = observed.get((animal_id, current), set())
                settled = set(recorded) | farm_not_milked
                missing = [session for session in expected if session not in settled]
                if not missing:
                    continue
                conditions.append({
                    "dedupe_key": self.dedupe_key(current, animal_id),
                    "production_date": current.isoformat(),
                    "animal_id": animal_id,
                    "milking_frequency": snapshot.milking_frequency,
                    "expected_sessions": expected,
                    "recorded_sessions": [session for session in expected if session in recorded],
                    "farm_not_milked_sessions": [session for session in expected if session in farm_not_milked],
                    "missing_sessions": missing,
                    "schedule_source": snapshot.source,
                })
            current += timedelta(days=1)
        conditions.sort(key=lambda item: (item["production_date"], item["animal_id"]))
        return {"scan_start": start.isoformat(), "scan_end": end.isoformat(), "conditions": conditions}

    def inspect(self, *, as_of_date: date | None = None, lookback_days: int = 31) -> dict[str, Any]:
        scan = self._scan(as_of_date=as_of_date, lookback_days=lookback_days)
        existing = list(self.finding_repository.get_all() or [])
        by_key: dict[str, list[Any]] = defaultdict(list)
        for finding in existing:
            key = str(getattr(finding, "dedupe_key", "") or "")
            if key.startswith(f"{MISSED_DEDUPE_PREFIX}:"):
                by_key[key].append(finding)
        active: list[dict[str, Any]] = []
        rejected = 0
        for condition in scan["conditions"]:
            matches = by_key.get(condition["dedupe_key"], [])
            if self._explicitly_rejected(matches):
                rejected += 1
                continue
            open_finding = next(
                (
                    item for item in reversed(matches)
                    if _status(getattr(item, "status", None)) in OPEN_STATUSES
                ),
                None,
            )
            active.append({
                **condition,
                "finding_id": getattr(open_finding, "finding_id", None) if open_finding is not None else None,
                "severity": "HIGH",
                "status": "ACTION_REQUIRED",
            })
        return {
            "data_status": "LIVE_DERIVED_CONTROL",
            "scan_start": scan["scan_start"],
            "scan_end": scan["scan_end"],
            "active_count": len(active),
            "rejected_count": rejected,
            "active": active,
        }

    def reconcile(self, *, as_of_date: date | None = None, lookback_days: int = 31) -> dict[str, Any]:
        scan = self._scan(as_of_date=as_of_date, lookback_days=lookback_days)
        service = OperationalFindingService(self.finding_repository)
        existing = list(self.finding_repository.get_all() or [])
        by_key: dict[str, list[Any]] = defaultdict(list)
        for finding in existing:
            key = str(getattr(finding, "dedupe_key", "") or "")
            if key.startswith(f"{MISSED_DEDUPE_PREFIX}:"):
                by_key[key].append(finding)
        current_keys = {condition["dedupe_key"] for condition in scan["conditions"]}
        raised = updated = skipped_rejected = 0
        active: list[dict[str, Any]] = []
        for condition in scan["conditions"]:
            key = condition["dedupe_key"]
            matches = by_key.get(key, [])
            if self._explicitly_rejected(matches):
                skipped_rejected += 1
                continue
            had_open = any(
                _status(getattr(item, "status", None)) in OPEN_STATUSES
                for item in matches
            )
            missing_text = ", ".join(condition["missing_sessions"])
            recorded_text = ", ".join(condition["recorded_sessions"]) or "none"
            expected_text = ", ".join(condition["expected_sessions"])
            finding = service.raise_or_update(
                source_module="MILK",
                severity="HIGH",
                title="Missed milking entry",
                detail=(
                    f"Animal {condition['animal_id']} on {condition['production_date']} expected "
                    f"{expected_text}. Recorded: {recorded_text}. Missing: {missing_text}. "
                    "Enter the historical milk quantity if recoverable, or explicitly reject "
                    "the missing entry with an audited reason."
                ),
                subject_type="ANIMAL",
                subject_id=condition["animal_id"],
                route="/farm/milk",
                dedupe_key=key,
            )
            updated += int(had_open)
            raised += int(not had_open)
            by_key.setdefault(key, []).append(finding)
            active.append({
                **condition,
                "finding_id": finding.finding_id,
                "severity": finding.severity,
                "status": "ACTION_REQUIRED",
            })
        resolved = 0
        scan_start = _as_date(scan["scan_start"])
        scan_end = _as_date(scan["scan_end"])
        for finding in list(self.finding_repository.get_all() or []):
            key = str(getattr(finding, "dedupe_key", "") or "")
            finding_day = self._dedupe_date(key)
            if (
                not key.startswith(f"{MISSED_DEDUPE_PREFIX}:")
                or finding_day is None
                or scan_start is None
                or scan_end is None
                or finding_day < scan_start
                or finding_day > scan_end
                or key in current_keys
                or _status(getattr(finding, "status", None)) not in OPEN_STATUSES
            ):
                continue
            service.resolve(
                finding.finding_id,
                operator="SYSTEM",
                resolution_note=AUTO_RESOLUTION_NOTE,
            )
            resolved += 1
        return {
            "data_status": "LIVE_PERSISTED_CONTROL",
            "scan_start": scan["scan_start"],
            "scan_end": scan["scan_end"],
            "active_count": len(active),
            "raised_count": raised,
            "updated_count": updated,
            "resolved_count": resolved,
            "rejected_count": skipped_rejected,
            "active": active,
        }
