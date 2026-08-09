from dairyos.finance.cashflow.services.cash_flow_service import CashFlowService



def test_opening_cash():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.opening_cash == 5000000



def test_income():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.income == 4200000



def test_expenses():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.expenses == 3500000



def test_net_cash():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.net_cash_movement == 700000



def test_closing_cash():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.closing_cash == 5700000



def test_positive_status():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.status == "POSITIVE"



def test_positive_action():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.action == "Maintain current operations"



def test_negative_cash():

    result = CashFlowService().evaluate(

        100000,

        50000,

        200000

    )

    assert result.status == "NEGATIVE"



def test_negative_action():

    result = CashFlowService().evaluate(

        100000,

        50000,

        200000

    )

    assert result.action == "Immediate cash recovery required"



def test_cashflow_command():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.closing_cash == 5700000
