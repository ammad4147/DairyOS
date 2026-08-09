from dairyos.farm.command_center.models.farm_status_snapshot import (
    FarmStatusSnapshot,
)


class FarmStatusProjectionAssembler:
    """
    Projects farm operational state into
    Command Center status sections.

    No business rules.
    Only presentation mapping.
    """

    def assemble(
        self,
        *,
        farm_state,
    ):

        milk_summary = farm_state.get(
            "milk_production_summary",
            {},
        )

        milk = {
            "today_litres": milk_summary.get(
                "total_litres_today",
                0,
            ),
            "entries_today": milk_summary.get(
                "milking_events_count",
                0,
            ),
            "latest_shift": milk_summary.get(
                "last_milking_time",
            ),
            "operator": milk_summary.get(
                "last_operator",
            ),
            "animal_id": milk_summary.get(
                "last_animal_id",
            ),
            "status": (
                "RECORDED"
                if milk_summary.get(
                    "milking_events_count",
                    0,
                ) > 0
                else "PENDING"
            ),
        }


        feeding_status = farm_state.get(
            "feeding_status",
            {},
        )

        feeding = {
            "events_today": feeding_status.get(
                "events_today",
                0,
            ),
            "last_feed_type": feeding_status.get(
                "last_feed_type",
            ),
            "last_quantity_kg": feeding_status.get(
                "last_quantity_kg",
                0,
            ),
            "last_operator": feeding_status.get(
                "last_operator",
            ),
            "status": (
                "RECORDED"
                if feeding_status.get(
                    "events_today",
                    0,
                ) > 0
                else "PENDING"
            ),
        }


        health_alerts = farm_state.get(
            "health_alerts",
            [],
        )

        severity_summary = {}

        for alert in health_alerts:

            severity = alert.get(
                "severity",
                "UNKNOWN",
            )

            severity_summary[severity] = (
                severity_summary.get(
                    severity,
                    0,
                )
                + 1
            )


        health = {
            "open_alerts": len(
                health_alerts,
            ),
            "severity_summary": severity_summary,
            "alerts": health_alerts,
            "status": (
                "ATTENTION_REQUIRED"
                if len(health_alerts) > 0
                else "NORMAL"
            ),
        }


        breeding_status = farm_state.get(
            "breeding_status",
            {},
        )

        breeding = {
            "events_today": breeding_status.get(
                "events_today",
                0,
            ),
            "last_event": breeding_status.get(
                "last_event",
            ),
            "animal_id": breeding_status.get(
                "animal_id",
            ),
            "status": (
                "RECORDED"
                if breeding_status.get(
                    "events_today",
                    0,
                ) > 0
                else "NO_ACTIVITY"
            ),
        }

        workforce_status = farm_state.get(
            "workforce_status",
            {},
        )


        workforce = {

            "events_today":
                workforce_status.get(
                    "events_today",
                    0,
                ),

            "last_activity":
                workforce_status.get(
                    "last_activity",
                ),

            "operator":
                workforce_status.get(
                    "operator",
                ),

            "status":
                (
                    "RECORDED"
                    if workforce_status.get(
                        "events_today",
                        0,
                    ) > 0
                    else "NO_ACTIVITY"
                ),

        }

        inventory_status = farm_state.get(
            "inventory_status",
            {},
        )


        inventory = {

            "items_tracked":
                inventory_status.get(
                    "items_tracked",
                    0,
                ),

            "alerts":
                inventory_status.get(
                    "alerts",
                    [],
                ),

            "last_update":
                inventory_status.get(
                    "last_update",
                ),

            "status":
                (
                    "ACTIVE"
                    if inventory_status.get(
                        "items_tracked",
                        0,
                    ) > 0
                    else "NO_ACTIVITY"
                ),

        }

        equipment_status = farm_state.get(
            "equipment_status",
            {},
        )


        equipment = {

            "assets_tracked":
                equipment_status.get(
                    "assets_tracked",
                    0,
                ),

            "active_issues":
                equipment_status.get(
                    "active_issues",
                    [],
                ),

            "last_check":
                equipment_status.get(
                    "last_check",
                ),

            "status":
                (
                    "ACTIVE"
                    if equipment_status.get(
                        "assets_tracked",
                        0,
                    ) > 0
                    else "NO_ACTIVITY"
                ),

        }

        financial_status = farm_state.get(
            "financial_status",
            {},
        )


        finance = {

            "cash_position":
                financial_status.get(
                    "cash_position",
                ),

            "monthly_expenses":
                financial_status.get(
                    "monthly_expenses",
                ),

            "alerts":
                financial_status.get(
                    "alerts",
                    [],
                ),

            "status":
                (
                    "ACTIVE"
                    if financial_status
                    else "NO_ACTIVITY"
                ),

        }

        return FarmStatusSnapshot(

            milk=milk,

            feeding=feeding,

            breeding=breeding,

            health=health,

            workforce=workforce,

            inventory=inventory,

            equipment=equipment,

            finance=finance,
        )
