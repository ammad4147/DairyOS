from dairyos.feed.models import FeedInventoryTransaction


class FeedInventoryService:

    def __init__(self):
        self.transactions = []

    def add_transaction(
        self,
        transaction: FeedInventoryTransaction,
    ):
        self.transactions.append(transaction)

    def get_transactions(self):
        return self.transactions

    def calculate_balance(self, feed_id: str):

        balance = 0

        for transaction in self.transactions:

            if transaction.feed_id == feed_id:

                if transaction.transaction_type == "RECEIVE":
                    balance += transaction.quantity

                elif transaction.transaction_type == "ISSUE":
                    balance -= transaction.quantity

        return balance
