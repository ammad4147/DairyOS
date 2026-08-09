from dairyos.farm.operations.dashboard import (
    FarmCommandCenterService,
    MilkHealthSummaryService,
)


class FakeDashboardService:


    def build_dashboard(
        self,
    ):

        return {

            "milk_today": 500,

            "feed_quantity_today": 300,

            "feed_cost_today": 25000,

            "health_alerts": 2,

            "breeding_pending": 1,

            "attention_items": [],

            "milk_anomalies": 3,

            "milk_health_risks": 2,

            "milk_recommended_checks": [
                "Check feed intake"
            ],
        }



def test_command_center_builds_intelligence():

    center = FarmCommandCenterService(
        FakeDashboardService()
    ).build()


    assert center.milk_today == 500

    assert center.milk_anomalies == 3

    assert center.milk_health_risks == 2

    assert (
        "Check feed intake"
        in center.milk_recommended_checks
    )



def test_milk_health_summary_builder():

    summary = MilkHealthSummaryService().build(

        [
            {
                "severity": "HIGH",
                "recommended_checks": [
                    "Veterinary examination"
                ],
            }
        ]

    )


    assert summary.milk_anomalies == 1

    assert summary.milk_health_risks == 1

    assert (
        "Veterinary examination"
        in summary.recommended_checks
    )
