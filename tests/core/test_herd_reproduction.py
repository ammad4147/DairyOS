from datetime import date


from dairyos.herd.reproduction.models import (

    BreedingRecord,

    Pregnancy

)


from dairyos.herd.reproduction.services import (

    reproduction_service

)



def test_breeding_record():


    record = BreedingRecord(

        animal_id="HF-5001",

        service_date=date.today(),

        breeding_method="AI",

        semen_type="SEXED_HF",

        technician="AI Technician"

    )


    assert record.breeding_method == "AI"



def test_pregnancy_tracking():


    service = reproduction_service.ReproductionService()


    pregnancy = Pregnancy(

        animal_id="HF-5001",

        confirmed_date=date.today(),

        expected_calving_date=date.today(),

        status="CONFIRMED"

    )


    service.confirm_pregnancy(

        pregnancy

    )


    assert service.pregnancy_count() == 1
