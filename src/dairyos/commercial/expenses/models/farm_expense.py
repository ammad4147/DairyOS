from dataclasses import dataclass



@dataclass
class FarmExpense:


    expense_id: str

    category: str

    amount: float

    expense_type: str

    status: str

    action: str
