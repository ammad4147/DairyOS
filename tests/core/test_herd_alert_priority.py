from dairyos.herd.dashboard.services.alert_priority_service import AlertPriorityService



def test_alert_creation():

    alerts = AlertPriorityService().generate(

        health_alerts=1

    )

    assert len(alerts) == 1



def test_replacement_priority():

    alerts = AlertPriorityService().generate(

        replacement_shortage=True

    )

    assert alerts[0].priority == 1



def test_health_priority():

    alerts = AlertPriorityService().generate(

        health_alerts=2

    )

    assert alerts[0].category == "HEALTH"



def test_reproduction_priority():

    alerts = AlertPriorityService().generate(

        open_cows=5

    )

    assert alerts[0].category == "REPRODUCTION"



def test_alert_ordering():

    alerts = AlertPriorityService().generate(

        health_alerts=1,

        replacement_shortage=True

    )

    assert alerts[0].category == "REPLACEMENT"



def test_cockpit_alert_integration():

    alerts = AlertPriorityService().generate(

        replacement_shortage=True

    )

    assert len(alerts) == 1



def test_no_alerts():

    alerts = AlertPriorityService().generate()

    assert len(alerts) == 0



def test_owner_action_queue():

    alerts = AlertPriorityService().generate(

        open_cows=7

    )

    assert alerts[0].recommended_action == "Review open cow list"
