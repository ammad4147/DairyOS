from dairyos.finance.cockpit.services.owner_financial_cockpit_service import OwnerFinancialCockpitService



def test_profit():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.profit == 700000



def test_cash():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.cash_position == 5700000



def test_status():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.financial_status == "HEALTHY"



def test_action():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.owner_action == "Continue operations"



def test_revenue():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.revenue == 4200000



def test_expenses():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.expenses == 3500000



def test_cash_risk():

    result = OwnerFinancialCockpitService().evaluate(

        100000,

        200000,

        -50000

    )

    assert result.financial_status == "CASH RISK"



def test_cash_action():

    result = OwnerFinancialCockpitService().evaluate(

        100000,

        200000,

        -50000

    )

    assert result.owner_action == "Immediate intervention required"



def test_attention():

    result = OwnerFinancialCockpitService().evaluate(

        100000,

        100000,

        50000

    )

    assert result.financial_status == "ATTENTION"



def test_command():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.profit == 700000
