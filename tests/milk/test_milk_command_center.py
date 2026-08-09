from dairyos.milk.integration import (
    MilkCommandCenterService,
)


def test_milk_command_snapshot_normal():

    snapshot = MilkCommandCenterService().build_snapshot(

        today_litres=500,

        expected_litres=500,

    )

    assert snapshot.operational_status == "NORMAL"

    assert snapshot.variance_percentage == 0



def test_milk_command_snapshot_warning():

    snapshot = MilkCommandCenterService().build_snapshot(

        today_litres=400,

        expected_litres=600,

    )

    assert snapshot.operational_status == "WARNING"

    assert snapshot.variance_percentage == -33.33



def test_milk_health_attention():

    snapshot = MilkCommandCenterService().build_snapshot(

        today_litres=300,

        expected_litres=600,

        health_alerts=[

            "HF-021 Veterinary Examination"

        ],

    )


    assert snapshot.operational_status == "CRITICAL"

    assert (
        "Animal health attention required"
        in snapshot.attention_items
    )
