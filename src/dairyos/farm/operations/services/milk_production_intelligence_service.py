from datetime import date as date_type, datetime as datetime_type

from dairyos.farm.operations.services.milk_production_intelligence import (
    MilkProductionIntelligence,
)


class MilkProductionIntelligenceService:
    """Generate milk-production intelligence from authoritative persisted data."""

    def __init__(
        self,
        operational_state_service,
        milk_repository=None,
    ):
        self.operational_state_service = operational_state_service
        self.milk_repository = milk_repository

    def _persisted_today(self, operational_date):
        """Aggregate the persisted MilkProduction rows for the operational day."""
        repository = self.milk_repository
        if repository is None:
            return None

        total_litres = 0.0
        shift_production = {
            "MORNING": 0.0,
            "AFTERNOON": 0.0,
            "EVENING": 0.0,
        }
        found = False

        for record in repository.get_all() or []:
            status = str(
                getattr(record, "status", "RECORDED") or "RECORDED"
            ).upper()
            if status == "VOID":
                continue

            production_date = getattr(record, "production_date", None)
            if production_date is None:
                continue

            if _as_date(production_date) != operational_date:
                continue

            found = True

            values = {
                "MORNING": getattr(record, "morning_yield", None),
                "AFTERNOON": getattr(record, "afternoon_yield", None),
                "EVENING": getattr(record, "evening_yield", None),
            }

            for session, value in values.items():
                if value is not None:
                    shift_production[session] += float(value or 0.0)

            total = getattr(record, "total_yield", None)
            if total is None:
                total = sum(float(value or 0.0) for value in values.values())
            total_litres += float(total or 0.0)

        if not found:
            return None

        return round(total_litres, 3), {
            key: round(value, 3)
            for key, value in shift_production.items()
        }

    def generate(self) -> MilkProductionIntelligence:
        state = self.operational_state_service.get_state()
        milk_status = state.milk_status

        total_litres = 0.0
        shift_production = {}
        completed_checkpoints = []
        operational_signals = []
        notes = []

        # The state projection remains the fallback for legacy/in-memory
        # callers. The live runtime attaches the persisted Milk repository,
        # making the database the authoritative source for current production.
        persisted = self._persisted_today(
            _as_date(getattr(state, "operational_date", None))
        )

        if persisted is not None:
            total_litres, shift_production = persisted
        else:
            for shift, record in milk_status.items():
                litres = record.get("litres", 0)
                total_litres += litres
                shift_production[shift] = litres

        for shift, record in milk_status.items():
            if record.get("status") == "completed":
                completed_checkpoints.append(shift)
            if shift_production.get(shift, 0.0) == 0:
                operational_signals.append(
                    {
                        "type": "ZERO_PRODUCTION_CHECKPOINT",
                        "checkpoint": shift,
                        "severity": "ATTENTION",
                    }
                )

        schedule_state = getattr(state, "schedule_state", None)
        expected_checkpoints = []
        if schedule_state is not None:
            expected_checkpoints = list(
                getattr(schedule_state, "milk_checkpoints", [])
            )

        missing_checkpoints = [
            checkpoint
            for checkpoint in expected_checkpoints
            if checkpoint not in completed_checkpoints
        ]

        if missing_checkpoints:
            operational_signals.append(
                {
                    "type": "MISSING_MILK_CHECKPOINT",
                    "checkpoints": missing_checkpoints,
                    "severity": "ATTENTION",
                }
            )
            notes.append(
                "Milk production entry incomplete for scheduled checkpoints."
            )

        production_status = (
            "VERIFIED" if not missing_checkpoints else "INCOMPLETE"
        )

        shift_contribution = {}
        if total_litres > 0:
            shift_contribution = {
                shift: (litres / total_litres) * 100
                for shift, litres in shift_production.items()
            }

        dominant_shift = (
            max(shift_production, key=shift_production.get)
            if shift_production
            else None
        )

        production_analytics = {
            "daily_total_litres": total_litres,
            "completed_checkpoints": len(completed_checkpoints),
            "expected_checkpoints": len(expected_checkpoints),
            "missing_checkpoints": len(missing_checkpoints),
            "dominant_shift": dominant_shift,
            "shift_count": len(shift_production),
        }

        return MilkProductionIntelligence(
            total_litres=total_litres,
            shift_production=shift_production,
            shift_contribution=shift_contribution,
            expected_checkpoints=expected_checkpoints,
            completed_checkpoints=completed_checkpoints,
            missing_checkpoints=missing_checkpoints,
            production_status=production_status,
            production_analytics=production_analytics,
            operational_signals=operational_signals,
            notes=notes,
        )

    def summary(self):
        return self.generate().summary()


def _as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime_type):
        return value.date()
    if isinstance(value, date_type):
        return value
    return date_type.fromisoformat(str(value)[:10])
