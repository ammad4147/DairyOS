from dataclasses import dataclass



@dataclass
class SimulationResult:

    scenario_name: str

    baseline_value: float

    simulated_value: float

    variance: float

    risk_level: str

