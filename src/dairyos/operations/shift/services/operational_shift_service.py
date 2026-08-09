from dairyos.operations.shift.models.operational_shift import (
    OperationalShift,
)


class OperationalShiftService:
    """
    Application service for operational shifts.

    Coordinates shift lifecycle while
    preserving operational continuity.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository


    def open_shift(
        self,
        shift_name: str,
        supervisor: str,
    ):

        shift = OperationalShift(

            shift_name=shift_name,

            supervisor=supervisor,

        )


        return self.repository.save(
            shift
        )


    def close_shift(
        self,
        shift_id: str,
        transferred_actions: int = 0,
    ):

        shift = self.repository.get(
            shift_id
        )


        if shift is None:
            return None


        shift.close(
            transferred_actions
        )


        return self.repository.save(
            shift
        )


    def latest_shift(
        self,
    ):

        return self.repository.latest()


    def all_shifts(
        self,
    ):

        return self.repository.all()
