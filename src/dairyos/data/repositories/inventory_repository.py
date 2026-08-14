from collections import defaultdict

from ..models.inventory_transaction import InventoryTransaction


class InventoryRepository:

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
                    InventoryTransaction
                ).all()
            )

        return self.records

    def get_by_id(self, record_id):

        if self.session:
            return (
                self.session.query(
                    InventoryTransaction
                )
                .filter(
                    InventoryTransaction.id == record_id
                )
                .first()
            )

        for item in self.records:
            if getattr(item, "id", None) == record_id:
                return item

        return None

    def exists(self, record_id):

        return self.get_by_id(record_id) is not None

    def count(self):

        if self.session:
            return (
                self.session.query(
                    InventoryTransaction
                ).count()
            )

        return len(self.records)

    def balance_by_item(self):
        """Current stock per item -- the signed sum of every movement ever
        recorded for it, never a separately-maintained running total.

        Returns a dict keyed by item name: {"transaction_count": int,
        "balance": float, "unit": str | None, "last_movement_at": datetime |
        None}. `unit` is taken from the most recent transaction that carried
        one; a running balance with no unit recorded anywhere is reported
        with `unit: None` rather than guessing.
        """

        totals: dict[str, float] = defaultdict(float)
        counts: dict[str, int] = defaultdict(int)
        units: dict[str, str | None] = {}
        last_seen: dict[str, object] = {}

        for row in self.get_all():
            totals[row.item] += float(row.signed_quantity or 0.0)
            counts[row.item] += 1

            if row.unit:
                units[row.item] = row.unit

            recorded_at = getattr(row, "recorded_at", None)
            if recorded_at is not None and (
                row.item not in last_seen
                or recorded_at >= last_seen[row.item]
            ):
                last_seen[row.item] = recorded_at

        return {
            item: {
                "transaction_count": counts[item],
                "balance": round(total, 3),
                "unit": units.get(item),
                "last_movement_at": (
                    last_seen[item].isoformat()
                    if last_seen.get(item) is not None
                    else None
                ),
            }
            for item, total in totals.items()
        }
