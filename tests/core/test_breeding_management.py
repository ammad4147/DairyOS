from dairyos.herd.breeding.services.breeding_management_service import BreedingManagementService



def test_animal_id():

    result = BreedingManagementService().evaluate(

        "HF-1030",

        "AI completed",

        pregnant=True

    )

    assert result.animal_id == "HF-1030"



def test_event_saved():

    result = BreedingManagementService().evaluate(

        "HF-1030",

        "AI completed",

        pregnant=True

    )

    assert result.breeding_event == "AI completed"



def test_pregnancy_confirmed():

    result = BreedingManagementService().evaluate(

        "HF-1030",

        "AI completed",

        pregnant=True

    )

    assert result.pregnancy_status == "PREGNANT"



def test_pregnancy_priority():

    result = BreedingManagementService().evaluate(

        "HF-1030",

        "AI completed",

        pregnant=True

    )

    assert result.priority == "NORMAL"



def test_calving_action():

    result = BreedingManagementService().evaluate(

        "HF-1030",

        "AI completed",

        pregnant=True

    )

    assert result.next_action == "Prepare calving schedule"



def test_ai_pending():

    result = BreedingManagementService().evaluate(

        "HF-1031",

        "AI completed",

        pregnant=False

    )

    assert result.pregnancy_status == "PENDING CONFIRMATION"



def test_pending_priority():

    result = BreedingManagementService().evaluate(

        "HF-1031",

        "AI completed",

        pregnant=False

    )

    assert result.priority == "MEDIUM"



def test_not_bred():

    result = BreedingManagementService().evaluate(

        "HF-1032",

        "No breeding",

        pregnant=False

    )

    assert result.pregnancy_status == "NOT BRED"



def test_not_bred_action():

    result = BreedingManagementService().evaluate(

        "HF-1032",

        "No breeding",

        pregnant=False

    )

    assert result.next_action == "Review breeding plan"



def test_breeding_flow():

    result = BreedingManagementService().evaluate(

        "HF-1033",

        "AI completed",

        pregnant=True

    )

    assert result.pregnancy_status == "PREGNANT"
