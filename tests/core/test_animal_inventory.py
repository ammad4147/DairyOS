from dairyos.herd.inventory.services.animal_inventory_service import AnimalInventoryService



def test_animal_id():

    result = AnimalInventoryService().evaluate(

        "HF-1025",

        "Holstein Friesian",

        26,

        "Pregnant Heifer"

    )

    assert result.animal_id == "HF-1025"



def test_breed():

    result = AnimalInventoryService().evaluate(

        "HF-1025",

        "Holstein Friesian",

        26,

        "Pregnant Heifer"

    )

    assert result.breed == "Holstein Friesian"



def test_age():

    result = AnimalInventoryService().evaluate(

        "HF-1025",

        "Holstein Friesian",

        26,

        "Pregnant Heifer"

    )

    assert result.age_months == 26



def test_category():

    result = AnimalInventoryService().evaluate(

        "HF-1025",

        "Holstein Friesian",

        26,

        "Pregnant Heifer"

    )

    assert result.category == "Pregnant Heifer"



def test_precalving_status():

    result = AnimalInventoryService().evaluate(

        "HF-1025",

        "Holstein Friesian",

        26,

        "Pregnant Heifer"

    )

    assert result.lifecycle_status == "PRE-CALVING"



def test_calf_status():

    result = AnimalInventoryService().evaluate(

        "HF-1026",

        "Holstein Friesian",

        6,

        "Calf"

    )

    assert result.lifecycle_status == "CALF"



def test_heifer_status():

    result = AnimalInventoryService().evaluate(

        "HF-1027",

        "Holstein Friesian",

        18,

        "Heifer"

    )

    assert result.lifecycle_status == "HEIFER"



def test_lactating_status():

    result = AnimalInventoryService().evaluate(

        "HF-1028",

        "Holstein Friesian",

        36,

        "Lactating Cow"

    )

    assert result.lifecycle_status == "LACTATING"



def test_asset_status():

    result = AnimalInventoryService().evaluate(

        "HF-1029",

        "Holstein Friesian",

        30,

        "Pregnant Heifer"

    )

    assert result.asset_status == "ACTIVE"



def test_inventory_flow():

    result = AnimalInventoryService().evaluate(

        "HF-1030",

        "Holstein Friesian",

        26,

        "Pregnant Heifer"

    )

    assert result.lifecycle_status == "PRE-CALVING"
