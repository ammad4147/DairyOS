from dairyos.operations.shift.models.operational_shift import (
    OperationalShift,
)


class OperationalShiftRepository:
    """
    In-memory repository for operational shifts.

    This mirrors the repository style used
    throughout DairyOS and can later be
    backed by persistent storage without
    changing callers.
    """


    def __init__(
        self,
    ):

        self._shifts = {}


    def save(
        self,
        shift: OperationalShift,
    ):

        self._shifts[
            shift.shift_id
        ] = shift

        return shift


    def get(
        self,
        shift_id: str,
    ):

        return self._shifts.get(
            shift_id
        )


    def all(
        self,
    ):

        return list(
            self._shifts.values()
        )


    def latest(
        self,
    ):

        if not self._shifts:
            return None

        return list(
            self._shifts.values()
        )[-1]
