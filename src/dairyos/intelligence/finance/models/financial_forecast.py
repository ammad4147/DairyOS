from dataclasses import dataclass



@dataclass
class FinancialForecast:


    period: str

    milk_output: float

    milk_price: float

    revenue: float

    expenses: float

    profit: float

    status: str
