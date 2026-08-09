from dataclasses import dataclass



@dataclass
class RiskForecast:


    category: str

    forecast: str

    probability: int

    risk_level: str

    recommended_action: str
