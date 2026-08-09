$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-074 Equipment Management Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\equipment\models",
"dairyos\equipment\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class EquipmentAsset:


    equipment_id: str

    equipment_name: str

    category: str

    operational_status: str

    maintenance_priority: str

    action: str
'@ | Set-Content `
"dairyos\equipment\models\equipment_asset.py"



@'
from ..models.equipment_asset import EquipmentAsset



class EquipmentManagementService:



    def evaluate(

        self,

        equipment_id,

        equipment_name,

        category,

        condition

    ):


        if condition.lower() == "good":

            operational_status = "OPERATIONAL"

            maintenance_priority = "NORMAL"

            action = "Continue scheduled maintenance"



        elif condition.lower() == "fair":

            operational_status = "OPERATIONAL"

            maintenance_priority = "MONITOR"

            action = "Schedule inspection"



        else:

            operational_status = "ATTENTION"

            maintenance_priority = "HIGH"

            action = "Immediate maintenance required"



        return EquipmentAsset(

            equipment_id,

            equipment_name,

            category,

            operational_status,

            maintenance_priority,

            action

        )
'@ | Set-Content `
"dairyos\equipment\services\equipment_management_service.py"



@'
from dairyos.equipment.services.equipment_management_service import EquipmentManagementService



def test_equipment_id():

    result = EquipmentManagementService().evaluate(

        "EQ-001",

        "Milk Chiller",

        "Cooling System",

        "Good"

    )

    assert result.equipment_id == "EQ-001"



def test_equipment_name():

    result = EquipmentManagementService().evaluate(

        "EQ-001",

        "Milk Chiller",

        "Cooling System",

        "Good"

    )

    assert result.equipment_name == "Milk Chiller"



def test_category():

    result = EquipmentManagementService().evaluate(

        "EQ-001",

        "Milk Chiller",

        "Cooling System",

        "Good"

    )

    assert result.category == "Cooling System"



def test_good_status():

    result = EquipmentManagementService().evaluate(

        "EQ-001",

        "Milk Chiller",

        "Cooling System",

        "Good"

    )

    assert result.operational_status == "OPERATIONAL"



def test_normal_priority():

    result = EquipmentManagementService().evaluate(

        "EQ-001",

        "Milk Chiller",

        "Cooling System",

        "Good"

    )

    assert result.maintenance_priority == "NORMAL"



def test_normal_action():

    result = EquipmentManagementService().evaluate(

        "EQ-001",

        "Milk Chiller",

        "Cooling System",

        "Good"

    )

    assert result.action == "Continue scheduled maintenance"



def test_fair_condition():

    result = EquipmentManagementService().evaluate(

        "EQ-002",

        "Generator",

        "Power System",

        "Fair"

    )

    assert result.maintenance_priority == "MONITOR"



def test_bad_condition():

    result = EquipmentManagementService().evaluate(

        "EQ-003",

        "Water Pump",

        "Water System",

        "Bad"

    )

    assert result.operational_status == "ATTENTION"



def test_bad_action():

    result = EquipmentManagementService().evaluate(

        "EQ-003",

        "Water Pump",

        "Water System",

        "Bad"

    )

    assert result.action == "Immediate maintenance required"



def test_equipment_flow():

    result = EquipmentManagementService().evaluate(

        "EQ-004",

        "Feed Mixer",

        "Feed Equipment",

        "Good"

    )

    assert result.operational_status == "OPERATIONAL"
'@ | Set-Content `
"tests\core\test_equipment_management.py"



Write-Host "HERD-074 Equipment Management Build Complete"