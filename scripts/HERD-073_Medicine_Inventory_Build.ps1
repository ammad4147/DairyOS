$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-073 Medicine Inventory Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\inventory\medicine\models",
"dairyos\inventory\medicine\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class MedicineInventory:


    medicine_name: str

    available_units: float

    monthly_consumption: float

    coverage_months: float

    status: str

    action: str
'@ | Set-Content `
"dairyos\inventory\medicine\models\medicine_inventory.py"



@'
from ..models.medicine_inventory import MedicineInventory



class MedicineInventoryService:



    def evaluate(

        self,

        medicine_name,

        available_units,

        monthly_consumption

    ):


        if monthly_consumption > 0:

            coverage_months = (

                available_units /

                monthly_consumption

            )

        else:

            coverage_months = 0



        if coverage_months >= 3:

            status = "SECURE"

            action = "Continue normal procurement"


        elif coverage_months >= 1:

            status = "MONITOR"

            action = "Review upcoming purchase"


        else:

            status = "CRITICAL"

            action = "Immediate medicine procurement required"



        return MedicineInventory(

            medicine_name,

            available_units,

            monthly_consumption,

            coverage_months,

            status,

            action

        )
'@ | Set-Content `
"dairyos\inventory\medicine\services\medicine_inventory_service.py"



@'
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
'@ | Set-Content `
"tests\core\test_medicine_inventory.py"



Write-Host "HERD-073 Medicine Inventory Build Complete"