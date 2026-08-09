from dairyos.farm.reproduction.models.pregnancy_record import (
    PregnancyRecord,
)

from dairyos.farm.reproduction.repository.reproduction_repository import (
    ReproductionRepository,
)

from dairyos.farm.reproduction.services.reproduction_management_service import (
    ReproductionManagementService,
)



def test_pregnancy_tracking():


    service = ReproductionManagementService(

        ReproductionRepository()

    )


    service.record_pregnancy(

        PregnancyRecord(

            pregnancy_id="P001",

            animal_id="HF001",

            confirmed=True,

            expected_calving_date="2027-01-01",

            checked_by="vet",

        )

    )


    assert len(
        service.pregnant_animals()
    ) == 1
