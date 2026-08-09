from dairyos.farm.health.models.health_record import (
    HealthRecord,
)

from dairyos.farm.health.repository.health_repository import (
    HealthRepository,
)

from dairyos.farm.health.services.health_management_service import (
    HealthManagementService,
)



def test_health_attention_detection():


    service = HealthManagementService(

        HealthRepository()

    )


    service.record_observation(

        HealthRecord(

            record_id="H001",

            animal_id="HF001",

            observation="mastitis signs",

            severity="high",

            recorded_by="worker",

        )

    )


    attention = (
        service.animals_needing_attention()
    )


    assert len(attention) == 1

    assert (
        attention[0].animal_id
        == "HF001"
    )
