from dairyos.herd.health.services.animal_baseline_service import (
    AnimalBaselineService
)

from dairyos.herd.health.services.animal_deviation_service import (
    AnimalDeviationService
)



def test_baseline_creation():

    result = AnimalBaselineService().create(

        "HF-8001",

        35,

        24,

        38.5,

        80,

        30

    )


    assert result.animal_id == "HF-8001"



def test_milk_deviation_high():

    result = AnimalDeviationService().evaluate_milk(

        35,

        25

    )


    assert result == "HIGH"



def test_feed_deviation_medium():

    result = AnimalDeviationService().evaluate_feed(

        24,

        21

    )


    assert result == "MEDIUM"



def test_normal_variation():

    result = AnimalDeviationService().evaluate_milk(

        30,

        29

    )


    assert result == "NORMAL"
