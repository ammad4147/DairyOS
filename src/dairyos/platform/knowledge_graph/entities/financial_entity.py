from dataclasses import dataclass



@dataclass
class FinancialEntity:

    transaction_id: str

    category: str

    amount: float

