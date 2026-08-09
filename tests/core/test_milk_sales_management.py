from dairyos.commercial.sales.services.milk_sales_management_service import MilkSalesManagementService



def test_sale_id():

    result = MilkSalesManagementService().evaluate(

        "SALE-001",

        625,

        225

    )

    assert result.sale_id == "SALE-001"



def test_quantity():

    result = MilkSalesManagementService().evaluate(

        "SALE-001",

        625,

        225

    )

    assert result.milk_quantity_litres == 625



def test_price():

    result = MilkSalesManagementService().evaluate(

        "SALE-001",

        625,

        225

    )

    assert result.selling_price_per_litre == 225



def test_daily_revenue():

    result = MilkSalesManagementService().evaluate(

        "SALE-001",

        625,

        225

    )

    assert result.daily_revenue == 140625



def test_active_status():

    result = MilkSalesManagementService().evaluate(

        "SALE-001",

        625,

        225

    )

    assert result.status == "ACTIVE"



def test_active_action():

    result = MilkSalesManagementService().evaluate(

        "SALE-001",

        625,

        225

    )

    assert result.action == "Continue milk sales operations"



def test_zero_sales():

    result = MilkSalesManagementService().evaluate(

        "SALE-002",

        0,

        225

    )

    assert result.status == "NO SALES"



def test_zero_sales_action():

    result = MilkSalesManagementService().evaluate(

        "SALE-002",

        0,

        225

    )

    assert result.action == "Review production or sales issue"



def test_revenue_flow():

    result = MilkSalesManagementService().evaluate(

        "SALE-003",

        100,

        225

    )

    assert result.daily_revenue == 22500



def test_sales_command():

    result = MilkSalesManagementService().evaluate(

        "SALE-004",

        625,

        225

    )

    assert result.status == "ACTIVE"
