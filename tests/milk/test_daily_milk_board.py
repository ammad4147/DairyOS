from dairyos.milk import (
    DailyMilkBoardService,
)



def test_daily_board_total():

    service = DailyMilkBoardService()


    board = service.create_board(
        "2026-07-22"
    )


    service.update_session(
        board,
        "MORNING",
        250
    )


    service.update_session(
        board,
        "EVENING",
        200
    )


    assert board.total_litres == 450



def test_daily_board_completion():

    service = DailyMilkBoardService()


    board = service.create_board(
        "2026-07-22"
    )


    service.update_animals(
        board,
        20,
        25
    )


    assert board.completion_percentage == 80



def test_average_yield():

    service = DailyMilkBoardService()


    board = service.create_board(
        "2026-07-22"
    )


    service.update_session(
        board,
        "MORNING",
        300
    )


    service.update_animals(
        board,
        15,
        15
    )


    assert board.average_yield == 20
