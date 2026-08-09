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


    def exists(self, record_id):

        return self.get_by_id(record_id) is not None


    def delete(self, record_id):

        if self.session:

            entity = self.get_by_id(record_id)

            if entity is None:
                return False

            self.session.delete(entity)
            self.session.commit()
            return True

        entity = self.get_by_id(record_id)

        if entity is None:
            return False

        self.records.remove(entity)
        return True


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
            if item.transaction_type == "INCOME"
        )


    def total_expenses(self):

        return sum(
            item.amount
            for item in self.get_all()
            if item.transaction_type == "EXPENSE"
        )


    def net_balance(self):

        return (
            self.total_income()
            -
            self.total_expenses()
        )
