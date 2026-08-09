from dataclasses import dataclass



@dataclass
class DailyOperations:


    milk_target: float

    milk_actual: float

    completed_tasks: int

    pending_tasks: int

    production_status: str

    overall_status: str
