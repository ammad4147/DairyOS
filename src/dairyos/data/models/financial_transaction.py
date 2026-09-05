from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)

from dairyos.core.time_utils import utcnow

from ..database.base import Base


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"
    __table_args__ = (
        Index(
            "uq_financial_transactions_payroll_record_id",
            "payroll_record_id",
            unique=True,
            postgresql_where=text("payroll_record_id IS NOT NULL AND COALESCE(status, 'RECORDED') <> 'VOID'"),
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    # Accounting authority: persist currency as fixed-point, never binary float.
    amount = Column(Numeric(18, 2), nullable=False)
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
    payroll_record_id = Column(Integer, nullable=True, index=True)
    status = Column(String, default="RECORDED")

    master_category = Column(String, nullable=True)
    sub_category = Column(String, nullable=True)
    custom_specification = Column(String, nullable=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    unit_rate = Column(Numeric(18, 6), nullable=True)

    due_date = Column(Date, nullable=True)
    settled_date = Column(Date, nullable=True)

    def is_income(self):
        from ...finance.classification import transaction_classifier
        return transaction_classifier.is_income(self)

    def is_expense(self):
        from ...finance.classification import transaction_classifier
        return transaction_classifier.is_expense(self)
