from datetime import datetime, timezone

from ..models.financial_transaction import FinancialTransaction


class FinancialRepository:


    def __init__(self, session=None):

        self.session = session
        self.records = []


    def add(self, transaction):

        if self.session:
            self.session.add(transaction)
            self.session.commit()
            self.session.refresh(transaction)
            return transaction

        self.records.append(transaction)
        return transaction


    def get_all(self):

        if self.session:
            return (
                self.session.query(
                    FinancialTransaction
                ).all()
            )

        return self.records


    def get_by_id(self, record_id):

        if self.session:
            return (
                self.session.query(
                    FinancialTransaction
                )
                .filter(
                    FinancialTransaction.id == record_id
                )
                .first()
            )

        for item in self.records:
            if getattr(item, "id", None) == record_id:
                return item

        return None


    def get_by_animal_id(self, animal_id):

        if not animal_id:
            return []

        if self.session:
            return (
                self.session.query(FinancialTransaction)
                .filter(FinancialTransaction.animal_id == str(animal_id))
                .all()
            )

        return [
            item for item in self.records
            if str(getattr(item, "animal_id", "")) == str(animal_id)
        ]


    def get_by_milk_sale_id(self, milk_sale_id):

        if not milk_sale_id:
            return []

        if self.session:
            return (
                self.session.query(FinancialTransaction)
                .filter(FinancialTransaction.milk_sale_id == str(milk_sale_id))
                .all()
            )

        return [
            item for item in self.records
            if str(getattr(item, "milk_sale_id", "")) == str(milk_sale_id)
        ]


    def exists(self, record_id):
        return self.get_by_id(record_id) is not None


    def delete(self, record_id):
        """Backward-compatible guard against destructive finance deletion."""
        raise RuntimeError(
            "Destructive deletion of financial transactions is prohibited. "
            "Use the governed VOID transition instead."
        )


    def void(self, record_id, reason=""):
        """Soft-void an unsettled financial transaction with an audit note."""
        entity = self.get_by_id(record_id)
        if entity is None:
            return False

        status = str(getattr(entity, "status", "RECORDED") or "RECORDED").upper()
        if status == "VOID":
            return entity
        if status in {"PAID", "RECEIVED"}:
            raise RuntimeError(
                f"Settled financial transactions in {status} state are immutable; "
                "use a governed correction entry instead."
            )

        cleaned_reason = (reason or "").strip()
        if not cleaned_reason:
            raise ValueError("A reason is required to void a financial transaction.")

        note = (getattr(entity, "notes", None) or "").strip()
        stamp = datetime.now(timezone.utc).isoformat()
        audit = f"VOIDED_AT={stamp} REASON={cleaned_reason}"
        entity.notes = f"{note}\n{audit}".strip()
        entity.status = "VOID"

        if self.session:
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
        return entity


    def count(self):

        if self.session:
            return (
                self.session.query(
                    FinancialTransaction
                ).count()
            )

        return len(self.records)


    def total_income(self):

        return sum(
            item.amount
            for item in self.get_all()
            if hasattr(item, "is_income") and item.is_income()
            or (not hasattr(item, "is_income") and getattr(item, "transaction_type", None) in ("INCOME", "RECEIPT"))
        )


    def total_expenses(self):

        return sum(
            item.amount
            for item in self.get_all()
            if hasattr(item, "is_expense") and item.is_expense()
            or (not hasattr(item, "is_expense") and getattr(item, "transaction_type", None) in ("EXPENSE", "PAYMENT"))
        )


    def net_balance(self):

        return (
            self.total_income()
            -
            self.total_expenses()
        )


    def get_animal_profitability(self, animal_id):
        """Calculate total income, expenses, and net profit for a specific animal."""
        records = self.get_by_animal_id(animal_id)

        income = sum(
            item.amount for item in records
            if hasattr(item, "is_income") and item.is_income()
            or getattr(item, "transaction_type", None) in ("INCOME", "RECEIPT")
        )

        expenses = sum(
            item.amount for item in records
            if hasattr(item, "is_expense") and item.is_expense()
            or getattr(item, "transaction_type", None) in ("EXPENSE", "PAYMENT")
        )

        return {
            "animal_id": str(animal_id),
            "total_income": income,
            "total_expenses": expenses,
            "net_profit": income - expenses,
        }
