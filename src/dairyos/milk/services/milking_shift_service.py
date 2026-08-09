from dairyos.milk.models.milking_shift import MilkingShift


class MilkingShiftService:


    def __init__(self):

        self.shifts: list[MilkingShift] = []


    def create_shift(
        self,
        shift: MilkingShift
    ):

        self.shifts.append(
            shift
        )


    def get_active_shifts(self):

        return [
            s
            for s in self.shifts
            if not s.closed
        ]


    def register_milking(
        self,
        shift_id: str,
        animal_id: str
    ):

        for shift in self.shifts:

            if shift.shift_id == shift_id:

                shift.register_animal(
                    animal_id
                )

                return True


        return False


    def close_shift(
        self,
        shift_id: str,
        operator: str
    ):

        for shift in self.shifts:

            if shift.shift_id == shift_id:

                shift.close_shift(
                    operator
                )

                return True


        return False
