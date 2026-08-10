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


    currency = Column(
        String,
        default="PKR",
        nullable=False
    )


    animal_id = Column(
        String,
        nullable=True
    )


    milk_sale_id = Column(
        String,
        nullable=True
    )


    feed_record_id = Column(
        String,
        nullable=True
    )


    status = Column(
        String,
        default="RECORDED"
    )


    def is_income(self):

        return self.transaction_type == "INCOME"



    def is_expense(self):

        return self.transaction_type == "EXPENSE"
