from dataclasses import dataclass



@dataclass
class FarmStatusSnapshot:

    farm_name: str

    departments: list

    metrics: list

