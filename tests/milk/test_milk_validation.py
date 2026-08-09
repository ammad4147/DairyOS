from dairyos.milk import (
    DailyMilkRegister,
    MilkValidationService,
    MilkEntry,
    MilkingSession,
)



def test_register_validation_failure():


    register = DailyMilkRegister(
        register_id="REG-001",
        date="2026-07-22",
    )


    service = MilkValidationService()


    problems = service.validate_register(
        register,
        10
    )


    assert len(problems) == 3



def test_register_ready():


    register = DailyMilkRegister(
        register_id="REG-002",
        date="2026-07-22",
    )


    register.add_entry(
        MilkEntry(
            entry_id="M001",
            animal_id="HF001",
            session=MilkingSession.MORNING,
            litres=15,
            operator="Worker"
        )
    )


    register.verify(
        "Supervisor"
    )


    service = MilkValidationService()


    assert service.is_ready(
        register,
        1
    ) is True
