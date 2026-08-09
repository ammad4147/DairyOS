from dairyos.milk.integration import (
    MilkCommandCenterService,
    MilkIntelligenceBridge,
)


def test_milk_normal_creates_low_priority_situation():

    snapshot = MilkCommandCenterService().build_snapshot(

        today_litres=500,

        expected_litres=500,

    )


    situation = MilkIntelligenceBridge().build_situation(
        snapshot
    )


    assert situation.status == "NORMAL"

    assert situation.priority == "LOW"



def test_milk_warning_creates_medium_priority_situation():

    snapshot = MilkCommandCenterService().build_snapshot(

        today_litres=400,

        expected_litres=600,

    )


    situation = MilkIntelligenceBridge().build_situation(
        snapshot
    )


    assert situation.status == "WARNING"

    assert situation.priority == "MEDIUM"



def test_milk_critical_creates_high_priority_situation():

    snapshot = MilkCommandCenterService().build_snapshot(

        today_litres=300,

        expected_litres=600,

    )


    situation = MilkIntelligenceBridge().build_situation(
        snapshot
    )


    assert situation.status == "CRITICAL"

    assert situation.priority == "HIGH"
