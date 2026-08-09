from datetime import date

from dairyos.application.dashboard.models.farm_today import (
    FarmTodaySnapshot,
)

from dairyos.application.dashboard.policies.dashboard_action_policy import (
    DashboardActionPolicy,
)


def test_overdue_tasks_generate_action():

    snapshot = FarmTodaySnapshot(

        snapshot_date=date.today(),

        overdue_tasks=3,

    )


    actions = (
        DashboardActionPolicy()
        .generate(snapshot)
    )


    assert len(actions) == 1

    assert (
        actions[0]
        .title
        ==
        "Review overdue tasks"
    )



def test_pending_tasks_generate_action():

    snapshot = FarmTodaySnapshot(

        snapshot_date=date.today(),

        pending_tasks=5,

    )


    actions = (
        DashboardActionPolicy()
        .generate(snapshot)
    )


    assert len(actions) == 1



def test_zero_milk_generates_recording_warning():

    snapshot = FarmTodaySnapshot(

        snapshot_date=date.today(),

        milk_total_litres=0,

    )


    actions = (
        DashboardActionPolicy()
        .generate(snapshot)
    )


    assert len(actions) == 1
