from datetime import datetime


from dairyos.herd.health.services.health_alert_service import (
    HealthAlertService
)

from dairyos.herd.health.models.health_follow_up import (
    HealthFollowUp
)

from dairyos.herd.health.services.health_follow_up_service import (
    HealthFollowUpService
)



def test_create_alert():

    result = HealthAlertService().create(

        "HF-12001",

        "MILK_DROP",

        "HIGH",

        "Production reduced",

        "Veterinarian"

    )


    assert result.status == "OPEN"



def test_open_alerts():

    service = HealthAlertService()


    service.create(

        "HF-12002",

        "FEED_DROP",

        "MEDIUM",

        "Feed intake reduction",

        "Manager"

    )


    assert len(service.get_open_alerts()) == 1



def test_followup_completion():

    service = HealthFollowUpService()


    followup = HealthFollowUp(

        "HF-12003",

        "ALERT-01",

        "Veterinary examination",

        "Vet",

        datetime.now(),

        False

    )


    service.create(followup)


    service.complete(followup)


    assert followup.completed is True
