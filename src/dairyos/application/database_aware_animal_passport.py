"""Database-scoped production implementation of the lifetime Animal Passport."""

from __future__ import annotations

from datetime import date

from dairyos.application.animal_passport import LifetimeAnimalPassportService
from dairyos.core.time_utils import utcnow


class DatabaseAwareLifetimeAnimalPassportService(LifetimeAnimalPassportService):
    """Use animal-scoped repository queries for history collections."""

    def _health_projection(self, animal_id: str, as_of_date: date):
        observations = self._through_date(
            self.factory.health().get_by_animal_id(animal_id),
            as_of_date,
        )
        cases = self._through_date(
            self.factory.health_cases().get_by_animal(animal_id),
            as_of_date,
        )
        treatments = self._through_date(
            self.factory.treatment().get_by_animal(animal_id),
            as_of_date,
        )
        open_cases = [
            case
            for case in cases
            if str(getattr(case, "status", "")).upper() == "OPEN"
        ]

        active_withdrawals = []
        for treatment in treatments:
            withdrawal_until = getattr(treatment, "milk_withdrawal_until", None)
            withdrawal_date = withdrawal_until.date() if hasattr(withdrawal_until, "date") else withdrawal_until
            if withdrawal_date is not None and withdrawal_date >= as_of_date:
                active_withdrawals.append(
                    {
                        "source": "TREATMENT",
                        "treatment_id": getattr(treatment, "id", None),
                        "medicine": getattr(treatment, "medicine", None),
                        "withdrawal_until": withdrawal_date.isoformat(),
                        "withdrawal_source": getattr(treatment, "withdrawal_source", None),
                    }
                )

        for case in cases:
            withdrawal_until = getattr(case, "withdrawal_until", None)
            withdrawal_date = withdrawal_until.date() if hasattr(withdrawal_until, "date") else withdrawal_until
            if withdrawal_date is not None and withdrawal_date >= as_of_date:
                active_withdrawals.append(
                    {
                        "source": "HEALTH_CASE",
                        "case_id": getattr(case, "case_id", None),
                        "withdrawal_until": withdrawal_date.isoformat(),
                    }
                )

        latest_observation = (
            max(observations, key=lambda item: self._record_date(item) or date.min)
            if observations
            else None
        )
        return {
            "summary": {
                "open_case_count": len(open_cases),
                "observation_count": len(observations),
                "treatment_count": len(treatments),
                "active_withdrawal": bool(active_withdrawals),
                "latest_observation_date": (
                    self._record_date(latest_observation).isoformat()
                    if latest_observation and self._record_date(latest_observation)
                    else None
                ),
                "latest_observation": (
                    getattr(latest_observation, "observation", None)
                    or getattr(latest_observation, "symptom", None)
                    if latest_observation
                    else None
                ),
            },
            "open_cases": [
                {
                    "case_id": getattr(case, "case_id", None),
                    "severity": getattr(case, "severity", None),
                    "diagnosis": getattr(case, "diagnosis", None),
                    "status": getattr(case, "status", None),
                    "opened_at": getattr(case, "opened_at", None).isoformat() if getattr(case, "opened_at", None) else None,
                    "follow_up_due_at": getattr(case, "follow_up_due_at", None).isoformat() if getattr(case, "follow_up_due_at", None) else None,
                    "withdrawal_until": getattr(case, "withdrawal_until", None).isoformat() if getattr(case, "withdrawal_until", None) else None,
                    "resolution": getattr(case, "resolution", None),
                }
                for case in open_cases
            ],
            "active_withdrawals": active_withdrawals,
        }

    def build(self, animal_id: str, as_of_date: date | None = None):
        animal = self.factory.animal().get_by_animal_id(animal_id)
        if animal is None:
            return None

        projection_date = as_of_date or utcnow().date()
        all_animals = self.factory.animal().get_all()
        lineage = self._lineage_projection(animal, all_animals)

        milk = self._through_date(
            self.factory.milk().get_by_animal_id(animal_id),
            as_of_date,
        )
        health = self._through_date(
            self.factory.health().get_by_animal_id(animal_id),
            as_of_date,
        )
        breeding = self._through_date(
            self.factory.breeding().get_by_animal_id(animal_id),
            as_of_date,
        )
        treatments = self._through_date(
            self.factory.treatment().get_by_animal(animal_id),
            as_of_date,
        )
        feed = self._through_date(
            self.factory.feed().get_by_animal_id(animal_id),
            as_of_date,
        )
        finance = self._through_date(
            self.factory.finance().get_by_animal_id(animal_id),
            as_of_date,
        )
        events = [
            event
            for event in self.factory.operational_events().get_all()
            if self._event_for_animal(event, animal_id)
            and (
                as_of_date is None
                or (
                    (event_date := self._record_date(event)) is not None
                    and event_date <= as_of_date
                )
            )
        ]

        history = {
            "milk": [self._serialize(item) for item in milk],
            "health": [self._serialize(item) for item in health],
            "breeding": [self._serialize(item) for item in breeding],
            "treatments": [self._serialize(item) for item in treatments],
            "feed": [self._serialize(item) for item in feed],
            "finance": [self._serialize(item) for item in finance],
            "operational_events": [self._serialize(item) for item in events],
            "lineage_descendants": [dict(item) for item in lineage["descendants"]],
        }

        timeline = [
            {
                "domain": domain,
                "timestamp": self._record_timestamp(record),
                "record": record,
            }
            for domain, records in history.items()
            for record in records
        ]
        timeline.sort(key=lambda item: str(item["timestamp"]))

        schedule = self._schedule_projection(animal, as_of_date)
        production = self._lactation_projection(milk, breeding, projection_date)
        reproduction = self._reproductive_projection(animal_id, breeding, projection_date)
        health_state = self._health_projection(animal_id, projection_date)
        biological_summary = {
            "lifetime_milk_liters": production["lifetime"]["lifetime_milk_liters"],
            "lactation_count": production["lifetime"]["lactation_count"],
            "lifetime_calvings": reproduction["summary"]["lifetime_calvings"],
            "current_reproductive_status": reproduction["summary"]["current_api_status"],
            "current_pregnancy_status": reproduction["summary"]["pregnancy_status"],
            "days_in_milk": reproduction["summary"]["days_in_milk"],
            "open_health_cases": health_state["summary"]["open_case_count"],
            "active_milk_withdrawal": health_state["summary"]["active_withdrawal"],
        }

        return {
            "animal": self._animal_identity(animal),
            "date_context": {
                "mode": "CURRENT_STATE" if as_of_date is None else "HISTORICAL_STATE",
                "operational_date": as_of_date.isoformat() if as_of_date is not None else None,
                "historical_state_basis": (
                    "Persisted domain records through the selected operational date plus effective-dated milking schedule authority."
                    if as_of_date is not None
                    else None
                ),
            },
            "lineage": lineage,
            "production": production,
            "reproduction": {
                "current": reproduction["summary"],
                "lifetime_events": reproduction["events"],
            },
            "health_state": health_state,
            "biological_summary": biological_summary,
            "schedule": schedule,
            "history": history,
            "timeline": timeline,
            "record_counts": {domain: len(records) for domain, records in history.items()},
        }
