from dairyos.herd.production.quality.services.milk_quality_service import MilkQualityService



def test_batch_id():

    result = MilkQualityService().evaluate(

        "MORNING-001",

        310,

        3.8,

        3.2

    )

    assert result.batch_id == "MORNING-001"



def test_volume():

    result = MilkQualityService().evaluate(

        "MORNING-001",

        310,

        3.8,

        3.2

    )

    assert result.volume_litres == 310



def test_fat_percentage():

    result = MilkQualityService().evaluate(

        "MORNING-001",

        310,

        3.8,

        3.2

    )

    assert result.fat_percentage == 3.8



def test_protein_percentage():

    result = MilkQualityService().evaluate(

        "MORNING-001",

        310,

        3.8,

        3.2

    )

    assert result.protein_percentage == 3.2



def test_good_status():

    result = MilkQualityService().evaluate(

        "MORNING-001",

        310,

        3.8,

        3.2

    )

    assert result.quality_status == "GOOD"



def test_premium_grade():

    result = MilkQualityService().evaluate(

        "MORNING-001",

        310,

        3.8,

        3.2

    )

    assert result.quality_grade == "PREMIUM"



def test_standard_quality():

    result = MilkQualityService().evaluate(

        "MORNING-002",

        300,

        3.3,

        2.9

    )

    assert result.quality_grade == "STANDARD"



def test_low_quality():

    result = MilkQualityService().evaluate(

        "MORNING-003",

        300,

        3.0,

        2.8

    )

    assert result.quality_status == "ATTENTION"



def test_quality_model():

    result = MilkQualityService().evaluate(

        "MORNING-004",

        250,

        3.6,

        3.1

    )

    assert result.quality_grade == "PREMIUM"



def test_quality_flow():

    result = MilkQualityService().evaluate(

        "MORNING-005",

        310,

        3.8,

        3.2

    )

    assert result.quality_status == "GOOD"
