from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)


class OperationalStateDashboardAdapter:
    """
    Compatibility adapter.

    Supports both:

    - FarmOperationalState (enterprise runtime)
    - FarmOperationalState runtime state

    External dashboard/API consumers depend only on this contract.
    """

    def __init__(
        self,
        state,
    ):
        self.state = state

    @property
    def is_enterprise_state(self):
        return isinstance(
            self.state,
            FarmOperationalState,
        )

    @property
    def farm_status(self):
        """Return the serialized farm status value, not the bound method."""
        operational_status = getattr(
            self.state,
            "operational_status",
            None,
        )

        if callable(operational_status):
            return operational_status()

        if operational_status is not None:
            return operational_status

        return getattr(
            self.state,
            "farm_status",
            "unknown",
        )

    @property
    def operational_date(self):
        return getattr(
            self.state,
            "operational_date",
            None,
        )

    @property
    def animals_source(self):
        animals = getattr(
            self.state,
            "animals",
            None,
        )

        if animals is not None:
            return animals

        if hasattr(self.state, "active_operations"):
            return self.state.active_operations.get(
                "animals",
                {},
            )

        return getattr(
            self.state,
            "animals",
            {},
        )

    @property
    def animals_count(self):
        return len(self.animals_source)

    @property
    def milking_animals(self):
        return len(
            [
                animal
                for animal in self.animals_source.values()
                if str(
                    animal.get("status", "")
                ).lower() == "milking"
            ]
        )

    @property
    def milking_percentage(self):
        if self.animals_count <= 0:
            return None

        return round(
            (self.milking_animals / self.animals_count) * 100,
            1,
        )

    @property
    def dry_animals(self):
        return len(
            [
                animal
                for animal in self.animals_source.values()
                if str(
                    animal.get("status", "")
                ).lower() == "dry"
            ]
        )

    @property
    def animals_needing_attention(self):
        animal_ids = {
            alert.get("animal_id")
            for alert in getattr(
                self.state,
                "health_alerts",
                [],
            )
            if alert.get("animal_id")
        }

        animal_ids.update(
            animal_id
            for animal_id, animal in self.animals_source.items()
            if animal.get("needs_attention")
        )

        return len(animal_ids)

    @property
    def health_active_exceptions(self):
        return self.animals_needing_attention

    @property
    def health_critical_cases(self):
        critical = 0

        for alert in getattr(
            self.state,
            "health_alerts",
            [],
        ):
            severity = str(
                alert.get("severity", "")
            ).upper()
            if severity == "CRITICAL":
                critical += 1

        for exception in getattr(
            self.state,
            "exceptions",
            [],
        ):
            severity = str(
                exception.get("severity", "")
                if isinstance(exception, dict)
                else getattr(exception, "severity", "")
            ).upper()
            if severity == "CRITICAL":
                critical += 1

        return critical

    @property
    def health_status(self):
        if self.health_critical_cases > 0:
            return "RED"
        if self.health_active_exceptions > 0:
            return "AMBER"
        return "GREEN"

    @property
    def milk_today(self):
        if hasattr(
            self.state,
            "milk_production_summary",
        ):
            return self.state.milk_production_summary.get(
                "total_litres_today",
                0,
            )

        return getattr(
            self.state,
            "milk_today",
            0,
        )

    @property
    def milk_events(self):
        if hasattr(
            self.state,
            "milk_production_summary",
        ):
            return self.state.milk_production_summary.get(
                "milking_events_count",
                0,
            )

        return getattr(
            self.state,
            "milk_events",
            0,
        )

    @property
    def milk_session_litres(self):
        milk_status = getattr(
            self.state,
            "milk_status",
            {},
        )

        result = {}
        for session in ("MORNING", "AFTERNOON", "EVENING"):
            entry = milk_status.get(session)
            if entry is None:
                entry = milk_status.get(session.lower())

            if isinstance(entry, dict):
                result[session] = entry.get("litres")

        return result

    @property
    def feed_today(self):
        if hasattr(
            self.state,
            "feeding_status",
        ):
            return sum(
                item.get(
                    "quantity_kg",
                    0,
                )
                for item in self.state.feeding_status.values()
                if isinstance(item, dict)
            )

        return getattr(
            self.state,
            "feed_today",
            0,
        )

    @property
    def feed_events(self):
        if hasattr(
            self.state,
            "feeding_status",
        ):
            return len(self.state.feeding_status)

        return getattr(self.state, "feed_events", 0)

    @property
    def last_operator(self):
        if hasattr(
            self.state,
            "milk_production_summary",
        ):
            return self.state.milk_production_summary.get(
                "last_operator"
            )

        return getattr(
            self.state,
            "last_operator",
            "",
        )

    @property
    def last_shift(self):
        if hasattr(
            self.state,
            "milk_production_summary",
        ):
            last_shift = self.state.milk_production_summary.get(
                "last_shift"
            )

            if last_shift:
                return last_shift

            milk_status = getattr(
                self.state,
                "milk_status",
                {},
            )

            if milk_status:
                return next(reversed(milk_status))

            return ""

        return getattr(
            self.state,
            "last_shift",
            "",
        )

    @property
    def last_feed_type(self):
        if hasattr(
            self.state,
            "feeding_status",
        ):
            return self.state.feeding_status.get(
                "last_feed_type",
                "",
            )

        return getattr(
            self.state,
            "last_feed_type",
            "",
        )

    @property
    def last_event_type(self):
        if hasattr(
            self.state,
            "operational_freshness",
        ):
            return self.state.operational_freshness.get(
                "event_type",
                "",
            )

        return getattr(
            self.state,
            "last_event_type",
            "",
        )

    @property
    def last_event_time(self):
        if hasattr(
            self.state,
            "operational_freshness",
        ):
            return self.state.operational_freshness.get(
                "timestamp",
                "",
            )

        return getattr(
            self.state,
            "last_event_time",
            "",
        )

    @property
    def exceptions(self):
        return getattr(
            self.state,
            "exceptions",
            [],
        )

    @property
    def total_events(self):
        return getattr(
            self.state,
            "total_events",
            0,
        )

    def snapshot(self):
        if hasattr(
            self.state,
            "summary",
        ):
            return self.state.summary()

        return self.state.to_dict()

    def to_dict(self):
        return self.snapshot()
