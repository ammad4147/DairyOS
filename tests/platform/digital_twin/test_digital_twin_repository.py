from dairyos.platform.digital_twin.persistence.repositories.digital_twin_repository import (
    DigitalTwinRepository,
)



def test_snapshot_persistence():


    repository = DigitalTwinRepository()



    snapshot = repository.save(

        farm_id="farm001",

        state={

            "milk":625

        },

        snapshot_type="daily",

    )



    assert snapshot.farm_id == "farm001"


    assert len(repository.history()) == 1


    assert repository.history()[0].state["milk"] == 625

