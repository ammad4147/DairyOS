from dataclasses import dataclass



@dataclass
class ProfitabilitySummary:


    revenue: float

    expenses: float

    operating_profit: float

    profit_margin: float

    status: str

    action: str
