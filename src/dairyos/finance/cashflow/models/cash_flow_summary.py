from dataclasses import dataclass



@dataclass
class CashFlowSummary:


    opening_cash: float

    income: float

    expenses: float

    net_cash_movement: float

    closing_cash: float

    status: str

    action: str
