from dataclasses import asdict

from dairyos.dashboard.assemblers.dashboard_projection_assembler import (
    DashboardProjectionAssembler,
)
from dairyos.farm.operations.state.operational_state_dashboard_adapter import (
    OperationalStateDashboardAdapter,
)


class DashboardProjectionService:
    """
    Produces the owner-facing DashboardView.

    Composition only.

    Owns no business logic.

    Herd counts are supplied from the authoritative persisted animal
    repository when the projection is built from the live application
    container.
    """

    def __init__(
        self,
        *,
        assembler=None,
    ):
        self.assembler = (
            assembler
            or DashboardProjectionAssembler()
        )

    def project(
        self,
        *,
        farm_state,
        dashboard=None,
        operational_decisions=None,
        decision_summary=None,
        exceptions=None,
        authoritative_animals=None,
    ):
        dashboard_view = (
            self.assembler.assemble()
        )

        dashboard_view.owner_attention = (
            self._owner_attention(
                operational_decisions,
                exceptions,
            )
        )

        self._populate_attention_zone(
            dashboard_view,
        )

        dashboard_view.quick_actions = (
            self._quick_actions()
        )

        dashboard_view.farm_timeline = (
            self._timeline(
                farm_state,
            )
        )

        dashboard_view.animal_spotlight = (
            self._animal_spotlight(
                farm_state,
            )
        )

        self._populate_milk_zone(
            dashboard_view,
            farm_state,
        )

        self._populate_herd_zone(
            dashboard_view,
            farm_state,
            authoritative_animals=authoritative_animals,
        )

        return dashboard_view

    def project_compatibility_dashboard(
        self,
        *,
        farm_state,
        event_journal,
        heads_up_notifications=None,
        operational_decisions=None,
        decision_summary=None,
        milk_read_model=None,
        feed_read_model=None,
        authoritative_animals=None,
    ):
        """Build the established dashboard dictionary from authoritative read models."""

        state = self._dashboard_state(
            farm_state,
            authoritative_animals=authoritative_animals,
        )

        milk_read_model = milk_read_model or {}
        feed_read_model = feed_read_model or {}

        milk_trend = (
            milk_read_model.get(
                "production_trend",
                {},
            )
            or {}
        )

        shift_production = (
            milk_read_model.get(
                "group_yield",
                {},
            )
            or {}
        ).get(
            "shift_production",
            {},
        ) or {}

        production_trend = (
            milk_read_model.get(
                "production_trend",
                {},
            )
        )

        comparison_status = (
            production_trend.get(
                "comparison_status"
            )
            if isinstance(
                production_trend,
                dict,
            )
            else None
        )

        return {
            "system": "DairyOS",
            "farm_status": state.farm_status,
            "operational_state": state.to_dict(),
            "animals": {
                "total": state.animals_count,
                "milking": state.milking_animals,
                "dry": state.dry_animals,
                "milking_percentage": (
                    state.milking_percentage
                ),
            },
            "milk": {
                "production_date": (
                    str(state.operational_date)
                    if state.operational_date is not None
                    else None
                ),
                "litres": milk_read_model.get(
                    "total_litres",
                    state.milk_today,
                ),
                "today_litres": milk_read_model.get(
                    "total_litres",
                    state.milk_today,
                ),
                "previous_production_date": (
                    milk_trend.get(
                        "prior_date"
                    )
                ),
                "previous_litres": (
                    milk_trend.get(
                        "prior_total_litres"
                    )
                ),
                "change_percent": (
                    milk_trend.get(
                        "variance_percentage"
                    )
                ),
                "comparison_status": (
                    comparison_status
                ),
                "morning_litres": (
                    shift_production.get(
                        "MORNING",
                        shift_production.get(
                            "morning"
                        ),
                    )
                ),
                "afternoon_litres": (
                    shift_production.get(
                        "AFTERNOON",
                        shift_production.get(
                            "afternoon"
                        ),
                    )
                ),
                "evening_litres": (
                    shift_production.get(
                        "EVENING",
                        shift_production.get(
                            "evening"
                        ),
                    )
                ),
                "events": state.milk_events,
                "last_operator": state.last_operator,
                "last_shift": state.last_shift,
            },
            "health": {
                "status": state.health_status,
                "active_exceptions": (
                    state.health_active_exceptions
                ),
                "critical_cases": (
                    state.health_critical_cases
                ),
            },
            "feed": {
                "today_kg": feed_read_model.get(
                    "today_kg",
                    state.feed_today,
                ),
                "events": feed_read_model.get(
                    "events",
                    state.feed_events,
                ),
                "last_feed_type": feed_read_model.get(
                    "last_feed_type",
                    state.last_feed_type,
                ),
            },
            "freshness": {
                "last_event": state.last_event_type,
                "last_event_time": state.last_event_time,
            },
            "heads_up_notifications": (
                heads_up_notifications or []
            ),
            "operational_decisions": (
                operational_decisions or []
            ),
            "operational_decision_summary": (
                decision_summary or {}
            ),
            "exceptions": state.exceptions,
            "event_count": event_journal.count(),
            "event_journal": {
                "total_events": event_journal.count(),
                "latest_events": event_journal.latest(),
            },
        }

    @staticmethod
    def _feed_read_model(container):
        """Build today's Feed projection from persisted FeedRecord data."""

        repository_factory = getattr(
            container,
            "repository_factory",
            None,
        )

        if repository_factory is None:
            return {}

        feed_repository = repository_factory.feed()
        records = feed_repository.get_all() or []

        farm_state_service = getattr(
            container,
            "farm_operational_state_service",
            None,
        )

        farm_state = (
            farm_state_service.get_state()
            if farm_state_service is not None
            else None
        )

        operational_date = getattr(
            farm_state,
            "operational_date",
            None,
        )

        if operational_date is None:
            return {}

        # Normalize the operational date and persisted DateTime values
        # to the same YYYY-MM-DD representation. The operational-state
        # boundary may provide a date object or a serialized ISO string.
        target_day = str(
            operational_date
        )[:10]

        matching = []

        for record in records:
            status = str(
                getattr(
                    record,
                    "status",
                    "RECORDED",
                )
                or "RECORDED"
            ).upper()

            if status == "VOID":
                continue

            feeding_date = getattr(
                record,
                "feeding_date",
                None,
            )

            if feeding_date is None:
                continue

            record_day = str(
                feeding_date.isoformat()
                if hasattr(
                    feeding_date,
                    "isoformat",
                )
                else feeding_date
            )[:10]

            if record_day == target_day:
                matching.append(record)

        total_kg = round(
            sum(
                float(
                    getattr(
                        record,
                        "quantity_kg",
                        0.0,
                    )
                    or 0.0
                )
                for record in matching
            ),
            3,
        )

        latest = max(
            matching,
            key=lambda record: str(
                getattr(
                    record,
                    "feeding_date",
                    "",
                )
                or ""
            ),
            default=None,
        )

        return {
            "today_kg": total_kg,
            "events": len(matching),
            "last_feed_type": (
                str(
                    getattr(
                        latest,
                        "feed_type",
                        "",
                    )
                    or ""
                )
                if latest is not None
                else ""
            ),
            "data_status": "LIVE_PERSISTED_DATA",
        }

    def project_compatibility_dashboard_from_container(
        self,
        container,
    ):
        """Collect runtime inputs and build the live dashboard projection."""

        farm_state = (
            container.farm_operational_state_service.get_state()
        )

        heads_up_notifications = (
            self._heads_up_notifications(
                container,
                farm_state,
            )
        )

        operational_decisions, decision_summary = (
            self._decisions(container)
        )

        milk_read_model = self._milk_read_model(
            container
        )

        feed_read_model = self._feed_read_model(
            container
        )

        authoritative_animals = (
            container.animal_repository.get_all()
        )

        return self.project_compatibility_dashboard(
            farm_state=farm_state,
            event_journal=container.event_journal,
            heads_up_notifications=heads_up_notifications,
            operational_decisions=operational_decisions,
            decision_summary=decision_summary,
            milk_read_model=milk_read_model,
            feed_read_model=feed_read_model,
            authoritative_animals=authoritative_animals,
        )

    def project_api_contract(
        self,
        container,
    ):
        """Build the current public API payload without route-level assembly."""

        farm_state = (
            container.farm_operational_state_service.get_state()
        )

        operational_decisions, decision_summary = (
            self._decisions(container)
        )

        authoritative_animals = (
            container.animal_repository.get_all()
        )

        dashboard_view = self.project(
            farm_state=farm_state,
            operational_decisions=operational_decisions,
            decision_summary=decision_summary,
            exceptions=farm_state.exceptions,
            authoritative_animals=authoritative_animals,
        )

        compatibility_dashboard = (
            self.project_compatibility_dashboard_from_container(
                container
            )
        )

        operational_state = farm_state.summary()

        # The FarmOperationalState remains authoritative for farm-operation
        # state, but its legacy animals projection is not the persisted animal
        # registry. The live animal repository is the authoritative source for
        # current animal identity, lifecycle and milking eligibility.
        #
        # Keep the public dashboard contract internally consistent by placing
        # the same authoritative animal projection into operational_state.
        operational_state["animals"] = (
            self._authoritative_animals_state(
                authoritative_animals
            )
        )

        return {
            "system": "DairyOS",
            "module": "Farm Command Center",
            "health": compatibility_dashboard[
                "health"
            ]["status"],
            "farm_status": (
                farm_state.operational_status()
            ),
            "operational_state": operational_state,
            "dashboard": compatibility_dashboard,
            "dashboard_view": asdict(
                dashboard_view
            ),
            "operational_decisions": (
                operational_decisions
            ),
            "operational_decision_summary": (
                decision_summary
            ),
            "exceptions": farm_state.exceptions,
            "event_count": (
                len(farm_state.exceptions)
                + farm_state.heads_up_count()
            ),
        }

    @staticmethod
    def _authoritative_animals_state(
        animals,
    ):
        """Serialize persisted animal records into the dashboard read contract."""

        result = {}

        for animal in animals or []:
            animal_id = getattr(
                animal,
                "animal_id",
                None,
            )

            if not animal_id:
                continue

            is_milking = bool(
                getattr(
                    animal,
                    "is_currently_milking",
                    False,
                )
            )

            result[str(animal_id)] = {
                "animal_id": str(animal_id),
                "animal_type": getattr(
                    animal,
                    "animal_type",
                    None,
                ),
                "breed": getattr(
                    animal,
                    "breed",
                    None,
                ),
                "sex": getattr(
                    animal,
                    "sex",
                    None,
                ),
                "lifecycle_status": getattr(
                    animal,
                    "lifecycle_status",
                    None,
                ),
                "status": (
                    "MILKING"
                    if is_milking
                    else "NON-MILKING"
                ),
                "is_currently_milking": is_milking,
                "milking_frequency": getattr(
                    animal,
                    "milking_frequency",
                    None,
                ),
                "production_group": getattr(
                    animal,
                    "production_group",
                    None,
                ),
                "location": getattr(
                    animal,
                    "location",
                    None,
                ),
                "active": bool(
                    getattr(
                        animal,
                        "active",
                        True,
                    )
                ),
                "non_milking_directive": getattr(
                    animal,
                    "non_milking_directive",
                    None,
                ),
                "non_milking_reason": getattr(
                    animal,
                    "non_milking_reason",
                    None,
                ),
                "non_milking_since": (
                    getattr(
                        animal,
                        "non_milking_since",
                        None,
                    ).isoformat()
                    if getattr(
                        animal,
                        "non_milking_since",
                        None,
                    )
                    else None
                ),
                "non_milking_until": (
                    getattr(
                        animal,
                        "non_milking_until",
                        None,
                    ).isoformat()
                    if getattr(
                        animal,
                        "non_milking_until",
                        None,
                    )
                    else None
                ),
            }

        return result
    @staticmethod
    def _dashboard_state(
        farm_state,
        *,
        authoritative_animals=None,
    ):
        if isinstance(
            farm_state,
            OperationalStateDashboardAdapter,
        ):
            if authoritative_animals is None:
                return farm_state

            return OperationalStateDashboardAdapter(
                farm_state.state,
                authoritative_animals=(
                    authoritative_animals
                ),
            )

        return OperationalStateDashboardAdapter(
            farm_state,
            authoritative_animals=(
                authoritative_animals
            ),
        )

    @staticmethod
    def _milk_read_model(container):
        """Read existing authoritative milk intelligence without recalculating it here."""

        service = getattr(
            container,
            "daily_milk_production_command_view_service",
            None,
        )

        if service is None:
            return {}

        try:
            return service.summary()
        except Exception:
            return {}

    @staticmethod
    def _heads_up_notifications(
        container,
        farm_state,
    ):
        service = getattr(
            container,
            "operational_heads_up_service",
            None,
        )

        if not service:
            return []

        return [
            notification.__dict__
            for notification in service.evaluate(
                farm_state
            )
        ]

    @staticmethod
    def _decisions(container):
        service = getattr(
            container,
            "operational_decision_service",
            None,
        )

        if not service:
            return [], {}

        return (
            service.evaluate(),
            service.priority_summary(),
        )

    def _populate_milk_zone(
        self,
        dashboard_view,
        farm_state,
    ):
        """Map live milk state into the dashboard's Milk zone."""

        state = self._dashboard_state(
            farm_state
        )

        values = {
            "milk.today": state.milk_today,
            "milk.shift": (
                state.last_shift
                or "No milk activity"
            ),
            "milk.operator": (
                state.last_operator
                or "No operator recorded"
            ),
        }

        for zone in dashboard_view.layout.zones:
            if zone.zone_id != "milk":
                continue

            for widget in zone.widgets:
                if widget.widget_id in values:
                    widget.value = values[
                        widget.widget_id
                    ]

            return

    def _populate_herd_zone(
        self,
        dashboard_view,
        farm_state,
        *,
        authoritative_animals=None,
    ):
        """Map live authoritative herd state into the dashboard Herd zone."""

        state = self._dashboard_state(
            farm_state,
            authoritative_animals=authoritative_animals,
        )

        values = {
            "herd.summary": state.animals_count,
            "herd.lactating": (
                state.milking_animals
            ),
            "herd.attention": (
                state.animals_needing_attention
            ),
        }

        for zone in dashboard_view.layout.zones:
            if zone.zone_id != "herd":
                continue

            for widget in zone.widgets:
                if widget.widget_id in values:
                    widget.value = values[
                        widget.widget_id
                    ]

            return

    def _populate_attention_zone(
        self,
        dashboard_view,
    ):
        for zone in dashboard_view.layout.zones:
            if zone.zone_id != "owner_attention":
                continue

            for widget in zone.widgets:
                if widget.widget_id == "owner.attention":
                    widget.value = (
                        dashboard_view.owner_attention
                    )

                    widget.has_alert = bool(
                        dashboard_view.owner_attention
                    )

            return

    def _owner_attention(
        self,
        decisions,
        exceptions,
    ):
        attention = []

        if decisions:
            attention.extend(
                decisions
            )

        if exceptions:
            attention.extend(
                exceptions
            )

        return attention

    def _quick_actions(
        self,
    ):
        return [
            {
                "id": "record_milk",
                "title": "Record Milk",
            },
            {
                "id": "feed_animals",
                "title": "Feed Animals",
            },
            {
                "id": "health_check",
                "title": "Health Check",
            },
            {
                "id": "record_treatment",
                "title": "Treatment",
            },
        ]

    def _timeline(
        self,
        farm_state,
    ):
        if not farm_state:
            return []

        return [
            {
                "event": "Current Operational Status",
                "status": (
                    farm_state.operational_status()
                ),
            }
        ]

    def _animal_spotlight(
        self,
        farm_state,
    ):
        return []

