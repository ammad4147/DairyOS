from dairyos.milk import (
    MilkingShift,
    MilkingShiftService,
    MilkingSession,
)



def test_create_milking_shift():

    shift = MilkingShift(
        shift_id="SHIFT-001",
        session=MilkingSession.MORNING,
        expected_animals=[
            "HF-001",
            "HF-002",
        ],
    )

    assert len(
        shift.expected_animals
    ) == 2



def test_missing_animals_detection():

    shift = MilkingShift(
        shift_id="SHIFT-002",
        session=MilkingSession.MORNING,
        expected_animals=[
            "HF-001",
            "HF-002",
        ],
    )


    shift.register_animal(
        "HF-001"
    )


    assert shift.missing_animals() == [
        "HF-002"
    ]



def test_shift_completion():

    service = MilkingShiftService()


    shift = MilkingShift(
        shift_id="SHIFT-003",
        session=MilkingSession.EVENING,
        expected_animals=[
            "HF-001"
        ],
    )


    service.create_shift(
        shift
    )


    service.register_milking(
        "SHIFT-003",
        "HF-001"
    )


    assert service.close_shift(
        "SHIFT-003",
        "Supervisor"
    ) is True
