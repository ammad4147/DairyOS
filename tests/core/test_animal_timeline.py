from datetime import datetime


from dairyos.herd.health.services.animal_timeline_service import (
    AnimalTimelineService
)

from dairyos.herd.health.services.animal_health_summary_service import (
    AnimalHealthSummaryService
)

from dairyos.herd.health.models.animal_health_event import (
    AnimalHealthEvent
)



def test_event_added():

    service = AnimalTimelineService()


    event = AnimalHealthEvent(

        "HF-10001",

        "HEALTH_SIGNAL",

        "Milk reduction detected",

        "Milking System",

        datetime.now(),

        "HIGH"

    )


    result = service.add_event(event)


    assert result.animal_id == "HF-10001"



def test_timeline_retrieval():

    service = AnimalTimelineService()


    service.add_event(

        AnimalHealthEvent(

            "HF-10002",

            "VACCINATION",

            "FMD vaccine",

            "Veterinarian",

            datetime.now(),

            "NORMAL"

        )

    )


    result = service.get_timeline(

        "HF-10002"

    )


    assert len(result) == 1



def test_health_summary():

    result = AnimalHealthSummaryService().build(

        "HF-10003",

        ["mastitis history"],

        ["AI failure"],

        ["milk drop"]

    )


    assert result["requires_review"] is True
