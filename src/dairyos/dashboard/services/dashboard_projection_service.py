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
    Owns no calculations.
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
    ):
        """Build the established dashboard dictionary for existing clients."""

        state = self._dashboard_state(farm_state)

        return {
            "system": "DairyOS",
            "farm_status": state.farm_status,
            "operational_state": state.to_dict(),
            "animals": {
                "total": state.animals_count,
                "milking": state.milking_animals,
                "dry": state.dry_animals,
            },
            "milk": {
                "today_litres": state.milk_today,
                "events": state.milk_events,
                "last_operator": state.last_operator,
                "last_shift": state.last_shift,
            },
            "feed": {
                "today_kg": state.feed_today,
                "events": state.feed_events,
                "last_feed_type": state.last_feed_type,
            },
            "freshness": {
                "last_event": state.last_event_type,
                "last_event_time": state.last_event_time,
            },
            "heads_up_notifications": heads_up_notifications or [],
            "operational_decisions": operational_decisions or [],
            "operational_decision_summary": decision_summary or {},
            "exceptions": state.exceptions,
            "event_count": event_journal.count(),
            "event_journal": {
                "total_events": event_journal.count(),
                "latest_events": event_journal.latest(),
            },
        }

    def project_compatibility_dashboard_from_container(
        self,
        container,
    ):
        """Collect runtime inputs and build the legacy dashboard projection."""

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

        return self.project_compatibility_dashboard(
            farm_state=farm_state,
            event_journal=container.event_journal,
            heads_up_notifications=heads_up_notifications,
            operational_decisions=operational_decisions,
            decision_summary=decision_summary,
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

        dashboard_view = self.project(
            farm_state=farm_state,
            operational_decisions=operational_decisions,
            decision_summary=decision_summary,
            exceptions=farm_state.exceptions,
        )

        return {
            "system": "DairyOS",
            "module": "Farm Command Center",
            "health": (
                "GREEN"
                if not farm_state.exceptions
                else "AMBER"
            ),
            "farm_status": farm_state.operational_status(),
            "operational_state": farm_state.summary(),
            "dashboard": (
                self.project_compatibility_dashboard_from_container(
                    container
                )
            ),
            "dashboard_view": asdict(dashboard_view),
            "operational_decisions": operational_decisions,
            "operational_decision_summary": decision_summary,
            "exceptions": farm_state.exceptions,
            "event_count": (
                len(farm_state.exceptions)
                + farm_state.heads_up_count()
            ),
        }

    @staticmethod
    def _dashboard_state(farm_state):
        if isinstance(
            farm_state,
            OperationalStateDashboardAdapter,
        ):
            return farm_state

        return OperationalStateDashboardAdapter(
            farm_state
        )

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
    ):
        """Map live herd state into the dashboard's Herd zone."""

        state = self._dashboard_state(
            farm_state
        )

        values = {
            "herd.summary": state.animals_count,
            "herd.lactating": state.milking_animals,
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
                "status": farm_state.operational_status(),
            }
        ]

    def _animal_spotlight(
        self,
        farm_state,
    ):
        return []

