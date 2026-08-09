"""
Dashboard projection factory.
"""

from dairyos.farm.operations.state.operational_state_dashboard_adapter import (
    OperationalStateDashboardAdapter,
)


def build_dashboard(
    milk_repo,
    operational_state=None,
):
    """
    Build dashboard projection.

    The dashboard layer consumes the adapter contract.

    FarmOperationalState remains the operational
    source of truth.

    Dashboard reads through the FarmOperationalState adapter contract.
    """


    if operational_state:

        state = (
            operational_state
            if isinstance(
                operational_state,
                OperationalStateDashboardAdapter,
            )
            else OperationalStateDashboardAdapter(
                operational_state
            )
        )


        return {

            "farm_status":
                state.farm_status,


            "animals":
            {

                "total":
                    state.animals_count,

                "milking":
                    state.milking_animals,

                "dry":
                    state.dry_animals,

            },


            "milk":
            {

                "today_litres":
                    state.milk_today,

                "events":
                    state.milk_events,

                "last_operator":
                    state.last_operator,

                "last_shift":
                    state.last_shift,

            },


            "feed":
            {

                "today_kg":
                    state.feed_today,

                "events":
                    state.feed_events,

                "last_feed_type":
                    state.last_feed_type,

            },


            "freshness":
            {

                "last_event":
                    state.last_event_type,

                "last_event_time":
                    state.last_event_time,

            },


            "exceptions":
                state.exceptions,

        }



    return {

        "farm_status":
            "unknown"

    }


