from dairyos.herd.calves.services.calf_management_service import CalfManagementService



def test_animal_id():

    result = CalfManagementService().evaluate(

        "CALF-001",

        3,

        "Female"

    )

    assert result.animal_id == "CALF-001"



def test_age_tracking():

    result = CalfManagementService().evaluate(

        "CALF-001",

        3,

        "Female"

    )

    assert result.age_months == 3



def test_sex_tracking():

    result = CalfManagementService().evaluate(

        "CALF-001",

        3,

        "Female"

    )

    assert result.sex == "Female"



def test_pre_weaning_stage():

    result = CalfManagementService().evaluate(

        "CALF-001",

        3,

        "Female"

    )

    assert result.growth_stage == "PRE-WEANING"



def test_pre_weaning_priority():

    result = CalfManagementService().evaluate(

        "CALF-001",

        3,

        "Female"

    )

    assert result.priority == "HIGH"



def test_weaning_stage():

    result = CalfManagementService().evaluate(

        "CALF-002",

        6,

        "Female"

    )

    assert result.growth_stage == "WEANING"



def test_weaning_priority():

    result = CalfManagementService().evaluate(

        "CALF-002",

        6,

        "Female"

    )

    assert result.priority == "MEDIUM"



def test_growing_stage():

    result = CalfManagementService().evaluate(

        "CALF-003",

        10,

        "Female"

    )

    assert result.growth_stage == "GROWING CALF"



def test_action_exists():

    result = CalfManagementService().evaluate(

        "CALF-004",

        3,

        "Female"

    )

    assert len(result.action) > 0



def test_calf_flow():

    result = CalfManagementService().evaluate(

        "CALF-005",

        3,

        "Female"

    )

    assert result.growth_stage == "PRE-WEANING"
