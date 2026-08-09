from dairyos.herd.lifecycle.services.animal_lifecycle_service import AnimalLifecycleService



def test_calf_stage():

    animal = AnimalLifecycleService().evaluate(

        "HF-001",

        6

    )

    assert animal.stage == "CALF"



def test_heifer_stage():

    animal = AnimalLifecycleService().evaluate(

        "HF-002",

        18

    )

    assert animal.stage == "HEIFER"



def test_pregnant_heifer_stage():

    animal = AnimalLifecycleService().evaluate(

        "HF-003",

        26,

        pregnant=True

    )

    assert animal.stage == "PREGNANT HEIFER"



def test_pregnant_priority():

    animal = AnimalLifecycleService().evaluate(

        "HF-003",

        26,

        pregnant=True

    )

    assert animal.priority == "HIGH"



def test_maternity_action():

    animal = AnimalLifecycleService().evaluate(

        "HF-003",

        26,

        pregnant=True

    )

    assert "Prepare maternity area" in animal.required_actions



def test_lactating_stage():

    animal = AnimalLifecycleService().evaluate(

        "HF-004",

        36,

        lactating=True

    )

    assert animal.stage == "LACTATING COW"



def test_lactating_action():

    animal = AnimalLifecycleService().evaluate(

        "HF-004",

        36,

        lactating=True

    )

    assert "Monitor milk production" in animal.required_actions



def test_dry_stage():

    animal = AnimalLifecycleService().evaluate(

        "HF-005",

        40,

        dry=True

    )

    assert animal.stage == "DRY COW"



def test_animal_id_saved():

    animal = AnimalLifecycleService().evaluate(

        "HF-006",

        20

    )

    assert animal.animal_id == "HF-006"



def test_lifecycle_flow():

    animal = AnimalLifecycleService().evaluate(

        "HF-007",

        26,

        pregnant=True

    )

    assert animal.priority == "HIGH"
