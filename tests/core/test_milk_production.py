from dairyos.herd.production.services.milk_production_service import MilkProductionService



def test_group():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.animal_group == "Lactating Cows"



def test_animal_count():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.animal_count == 25



def test_expected_milk():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.expected_milk == 625



def test_actual_milk():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.actual_milk == 602



def test_negative_variance():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.variance == -23



def test_attention_status():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.status == "ATTENTION"



def test_target_status():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        600,

        650

    )

    assert result.status == "ON TARGET"



def test_positive_variance():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        600,

        650

    )

    assert result.variance == 50



def test_zero_variance():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        625

    )

    assert result.variance == 0



def test_production_flow():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.status == "ATTENTION"
