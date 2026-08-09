from dairyos.operations.shift.repositories.operational_shift_repository import (
    OperationalShiftRepository,
)

from dairyos.operations.shift.services.operational_shift_service import (
    OperationalShiftService,
)



def test_shift_open():

    repository = OperationalShiftRepository()

    service = OperationalShiftService(
        repository
    )


    shift = service.open_shift(
        shift_name="morning",
        supervisor="farm_manager",
    )


    assert shift.status == "open"

    assert shift.shift_name == "morning"

    assert shift.supervisor == "farm_manager"



def test_shift_close_with_handover():

    repository = OperationalShiftRepository()

    service = OperationalShiftService(
        repository
    )


    shift = service.open_shift(
        shift_name="evening",
        supervisor="supervisor",
    )


    closed = service.close_shift(
        shift_id=shift.shift_id,
        transferred_actions=3,
    )


    assert closed.status == "closed"

    assert closed.transferred_actions == 3

    assert closed.closed_at is not None
