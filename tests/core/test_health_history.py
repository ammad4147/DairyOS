from datetime import date


from dairyos.herd.health.services.health_history_service import (
    HealthHistoryService
)

from dairyos.herd.health.models.historical_health_record import (
    HistoricalHealthRecord
)

from dairyos.herd.health.models.vaccination_history import (
    VaccinationHistory
)



def test_previous_health_record_saved():

    service = HealthHistoryService()


    record = HistoricalHealthRecord(

        "HF-7001",

        "Mastitis",

        date.today(),

        "Previous treatment",

        "Recovered",

        "Previous Farm",

        False

    )


    result = service.add_history_record(record)


    assert result.condition == "Mastitis"



def test_previous_history_retrieved():

    service = HealthHistoryService()


    service.add_history_record(

        HistoricalHealthRecord(

            "HF-7002",

            "Ketosis",

            date.today(),

            "Treatment",

            "Recovered",

            "Previous Farm",

            False

        )

    )


    result = service.get_animal_history(

        "HF-7002"

    )


    assert len(result) == 1



def test_vaccination_history_saved():

    service = HealthHistoryService()


    vaccination = VaccinationHistory(

        "HF-7003",

        "FMD",

        date.today(),

        date.today(),

        "Previous Farm",

        False

    )


    result = service.add_vaccination_history(

        vaccination

    )


    assert result.vaccine_name == "FMD"



def test_health_timeline_contains_history():

    from dairyos.herd.health.services.animal_health_timeline_service import (
        AnimalHealthTimelineService
    )


    result = AnimalHealthTimelineService().build(

        "HF-7004",

        ["old record"],

        ["new observation"]

    )


    assert result["history_available"] is True
