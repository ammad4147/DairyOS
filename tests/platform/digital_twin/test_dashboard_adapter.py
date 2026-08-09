from dairyos.platform.digital_twin.presentation.services.dashboard_adapter import (
    DashboardAdapter,
)



def test_dashboard_generation():


    adapter = DashboardAdapter()



    dashboard = adapter.build(

        farm_id="farm001",

        current_state={

            "milk":625

        },

        forecasts={

            "milk":650

        },

        simulations={

            "feed_cost":"+15%"

        },

        signals=[

            "feed_review"

        ],

    )



    assert dashboard.farm_id == "farm001"


    assert dashboard.current_state["milk"] == 625


    assert len(dashboard.decision_signals) == 1

