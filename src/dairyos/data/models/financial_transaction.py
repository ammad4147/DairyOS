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


    # Added 2026-08-14 (Phase 1). Before this, the API accepted
    # payment_method, counterparty and notes, returned 200, and then
    # discarded all three: only a single `reference` field was persisted,
    # populated as `counterparty or notes or ""`, so an entry carrying both
    # a counterparty and notes lost the notes outright, and payment_method
    # was never stored in the ledger at all.
    #
    # payment_method is the field that makes "Cash in Hand vs Money at
    # Bank" possible on the dashboard. Its absence is why
    # financial_intelligence.reconciliation still carries a note saying it
    # "never infers account location from transaction text".
    #
    # All three are nullable with no default: rows written before the
    # migration genuinely did not record them, and NULL says so honestly
    # rather than inventing a value. `reference` is still populated as
    # before so nothing reading it breaks.
    payment_method = Column(
        String,
        nullable=True
    )


    counterparty = Column(
        String,
        nullable=True
    )


    notes = Column(
        String,
        nullable=True
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
        """Money in that counts as farm revenue (INCOME or RECEIPT).

        Delegates to the shared classifier so this agrees with every
        reporting surface. Previously this matched the literal string
        "INCOME" only, which silently excluded RECEIPT.
        """
        from ...finance.classification import transaction_classifier

        return transaction_classifier.is_income(self)


    def is_expense(self):
        """Money out that is a cost of running the farm (EXPENSE or PAYMENT).

        Deliberately excludes OWNER_WITHDRAWAL and LOAN_PAYMENT — real
        money out, but not farm costs; counting them would inflate cost
        per litre. See the classifier module docstring.
        """
        from ...finance.classification import transaction_classifier

        return transaction_classifier.is_expense(self)
