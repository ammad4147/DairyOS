from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    transaction_date = Column(DateTime, default=utcnow, nullable=False)
    reference = Column(String, default="")

    payment_method = Column(String, nullable=True)
    counterparty = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    currency = Column(String, default="PKR", nullable=False)
    animal_id = Column(
        String,
        ForeignKey("animal.animal_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    milk_sale_id = Column(String, nullable=True)
    feed_record_id = Column(String, nullable=True)
    status = Column(String, default="RECORDED")

    master_category = Column(String, nullable=True)
    sub_category = Column(String, nullable=True)
    custom_specification = Column(String, nullable=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    unit_rate = Column(Float, nullable=True)

    due_date = Column(Date, nullable=True)
    settled_date = Column(Date, nullable=True)

    def is_income(self):
        from ...finance.classification import transaction_classifier
        return transaction_classifier.is_income(self)

    def is_expense(self):
        from ...finance.classification import transaction_classifier
        return transaction_classifier.is_expense(self)
