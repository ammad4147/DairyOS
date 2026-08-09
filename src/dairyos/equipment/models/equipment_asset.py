from dataclasses import dataclass



@dataclass
class EquipmentAsset:


    equipment_id: str

    equipment_name: str

    category: str

    operational_status: str

    maintenance_priority: str

    action: str
