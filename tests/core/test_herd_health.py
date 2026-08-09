from datetime import date


from dairyos.herd.health.models import (

    HealthRecord,

    Vaccination

)


from dairyos.herd.health.services.health_service import (

    HealthService

)



def test_health_record_creation():


    record = HealthRecord(

        animal_id="HF-6001",

        event_date=date.today(),

        diagnosis="MASTITIS",

        treatment="ANTIBIOTIC",

        veterinarian="Farm Vet",

        status="RECOVERED"

    )


    assert record.diagnosis == "MASTITIS"



def test_vaccination_tracking():


    service = HealthService()


    vaccination = Vaccination(

        animal_id="HF-6001",

        vaccine_name="FMD",

        vaccination_date=date.today(),

        next_due_date=date.today()

    )


    service.add_vaccination(

        vaccination

    )


    assert service.vaccination_count() == 1



def test_health_service_record():


    service = HealthService()


    record = HealthRecord(

        animal_id="HF-6002",

        event_date=date.today(),

        diagnosis="FEVER",

        treatment="MEDICINE",

        veterinarian="Farm Vet",

        status="OPEN"

    )


    service.add_health_record(record)


    assert service.health_event_count() == 1
