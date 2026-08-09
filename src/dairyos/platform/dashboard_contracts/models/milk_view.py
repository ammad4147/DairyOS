from dataclasses import dataclass



@dataclass
class MilkProductionView:

    today_litres: float

    yesterday_litres: float

    average_yield: float

