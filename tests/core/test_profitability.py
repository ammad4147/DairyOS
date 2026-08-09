from dairyos.finance.profitability.services.profitability_service import ProfitabilityService



def test_revenue():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert result.revenue == 4200000



def test_expenses():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert result.expenses == 3500000



def test_operating_profit():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert result.operating_profit == 700000



def test_profit_margin():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert round(result.profit_margin, 2) == 16.67



def test_profitable_status():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert result.status == "PROFITABLE"



def test_profitable_action():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert result.action == "Continue current strategy"



def test_break_even():

    result = ProfitabilityService().evaluate(

        1000000,

        1000000

    )

    assert result.status == "BREAK EVEN"



def test_loss():

    result = ProfitabilityService().evaluate(

        100000,

        200000

    )

    assert result.status == "LOSS"



def test_loss_action():

    result = ProfitabilityService().evaluate(

        100000,

        200000

    )

    assert result.action == "Immediate corrective action required"



def test_profitability_command():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert result.operating_profit == 700000
