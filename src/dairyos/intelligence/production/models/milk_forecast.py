from dataclasses import dataclass



@dataclass
class MilkForecast:


    group_id: str

    current_output: float

    historical_average: float

    forecast_output: float

    trend: str

    status: str
