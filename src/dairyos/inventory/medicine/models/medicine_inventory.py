from dataclasses import dataclass



@dataclass
class MedicineInventory:


    medicine_name: str

    available_units: float

    monthly_consumption: float

    coverage_months: float

    status: str

    action: str
