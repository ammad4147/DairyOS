from dataclasses import dataclass


@dataclass
class DigitalTwinDashboard:

    farm_id: str

    current_state: dict

    forecast_summary: dict

    scenario_summary: dict

    decision_signals: list
