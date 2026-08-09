from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from ..database.base import Base


class FinancialTransaction(Base):


    __tablename__ = "financial_transactions"


    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )


    transaction_type = Column(
        String,
        nullable=False
    )


    category = Column(
        String,
        nullable=False
    )


    amount = Column(
        Float,
        nullable=False
    )


    transaction_date = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )


    reference = Column(
        String,
        default=""
    )


    status = Column(
        String,
        default="RECORDED"
    )


    def is_income(self):

        return self.transaction_type == "INCOME"



    def is_expense(self):

        return self.transaction_type == "EXPENSE"
