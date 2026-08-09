from dataclasses import dataclass


@dataclass
class FinancialCommand:
    """
    Dashboard command view for financial operations.

    Read model only.

    Financial calculations remain
    owned by financial services.
    """

    daily_revenue: float = 0.0

    daily_expense: float = 0.0

    cash_position: float = 0.0

    milk_income: float = 0.0

    feed_cost: float = 0.0

    financial_alerts: list = None

    def __post_init__(self):
        if self.financial_alerts is None:
            self.financial_alerts = []
