from dairyos.milk.models.daily_milk_board import DailyMilkBoard


class DailyMilkBoardService:


    def create_board(
        self,
        date: str
    ):

        return DailyMilkBoard(
            date=date
        )


    def update_session(
        self,
        board: DailyMilkBoard,
        session,
        litres: float
    ):


        if session == "MORNING":

            board.morning_litres = litres


        elif session == "AFTERNOON":

            board.afternoon_litres = litres


        elif session == "EVENING":

            board.evening_litres = litres


        else:

            raise ValueError(
                "Unknown milking session"
            )


    def update_animals(
        self,
        board: DailyMilkBoard,
        milked: int,
        expected: int
    ):

        board.animals_milked = milked

        board.expected_animals = expected
