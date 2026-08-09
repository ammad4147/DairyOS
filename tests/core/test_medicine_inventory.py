from dairyos.inventory.medicine.services.medicine_inventory_service import MedicineInventoryService



def test_medicine_name():

    result = MedicineInventoryService().evaluate(

        "Mastitis Treatment",

        45,

        5

    )

    assert result.medicine_name == "Mastitis Treatment"



def test_available_units():

    result = MedicineInventoryService().evaluate(

        "Mastitis Treatment",

        45,

        5

    )

    assert result.available_units == 45



def test_monthly_consumption():

    result = MedicineInventoryService().evaluate(

        "Mastitis Treatment",

        45,

        5

    )

    assert result.monthly_consumption == 5



def test_coverage_months():

    result = MedicineInventoryService().evaluate(

        "Mastitis Treatment",

        45,

        5

    )

    assert result.coverage_months == 9



def test_secure_status():

    result = MedicineInventoryService().evaluate(

        "Mastitis Treatment",

        45,

        5

    )

    assert result.status == "SECURE"



def test_secure_action():

    result = MedicineInventoryService().evaluate(

        "Mastitis Treatment",

        45,

        5

    )

    assert result.action == "Continue normal procurement"



def test_monitor_status():

    result = MedicineInventoryService().evaluate(

        "Mastitis Treatment",

        5,

        5

    )

    assert result.status == "MONITOR"



def test_critical_status():

    result = MedicineInventoryService().evaluate(

        "Mastitis Treatment",

        2,

        5

    )

    assert result.status == "CRITICAL"



def test_critical_action():

    result = MedicineInventoryService().evaluate(

        "Mastitis Treatment",

        2,

        5

    )

    assert result.action == "Immediate medicine procurement required"



def test_inventory_flow():

    result = MedicineInventoryService().evaluate(

        "Mastitis Treatment",

        45,

        5

    )

    assert result.coverage_months == 9
