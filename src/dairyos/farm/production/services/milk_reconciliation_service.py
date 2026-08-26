from __future__ import annotations

from datetime import date

from dairyos.data.models.milk_disposition import MilkDisposition
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
    MilkProductionTrendIntelligenceService,
)
from dairyos.farm.production.services.milk_finding_service import MilkFindingService


VALID_DISPOSITIONS = frozenset(
    {
        "SOLD",
        "CALF_FEED",
        "DOMESTIC_USE",
        "WASTAGE",
        "OTHER",
    }
)


class MilkReconciliationService:
    """Read/write boundary for daily milk destination accounting.

    Total biological production remains visible, but only saleable milk is
    available for ordinary destination accounting. Milk recorded under an
    active veterinary withdrawal is retained as production while excluded
    from saleable reconciliation.
    """

    def __init__(self, disposition_repository=None, production_repository=None):
        self.disposition_repository = disposition_repository
        self.production_repository = production_repository

    def _repo(self):
        if self.disposition_repository is not None:
            return self.disposition_repository, None

        factory = RepositoryFactory.create()
        return factory.milk_dispositions(), factory

    @staticmethod
    def _as_production_date(value):
        if value is None:
            return None
        if hasattr(value, "date"):
            return value.date()
        return value

    @classmethod
    def _production_total(cls, production_date: date, production_repository=None) -> dict:
        """Return biological and saleable production for one date.

        The persisted production repository is optional so isolated
        reconciliation tests can continue to exercise only the disposition
        contract. Production runtime supplies it to account for WITHDRAWAL
        milk explicitly.
        """
        trend = MilkProductionTrendIntelligenceService()
        snapshot = trend.generate(as_of_date=production_date, period_days=7).summary()

        complete = bool(snapshot.get("complete", snapshot.get("is_complete", False)))
        if not complete:
            return {
                "date": production_date.isoformat(),
                "complete": False,
                "daily_total": None,
                "total_litres": None,
                "saleable_litres": None,
                "withdrawal_litres": None,
            }

        daily_total = snapshot.get("daily_total")
        if daily_total is None:
            daily_total = snapshot.get("total_litres")
        if daily_total is None:
            daily_total = snapshot.get("total_yield")

        if daily_total is None:
            return {
                "date": production_date.isoformat(),
                "complete": False,
                "daily_total": None,
                "total_litres": None,
                "saleable_litres": None,
                "withdrawal_litres": None,
            }

        total = float(daily_total)
        saleable = total
        withdrawal = 0.0

        if production_repository is not None:
            dated_rows = []
            for row in production_repository.get_all():
                row_date = cls._as_production_date(getattr(row, "production_date", None))
                if row_date == production_date:
                    dated_rows.append(row)

            if dated_rows:
                row_total = 0.0
                row_withdrawal = 0.0
                for row in dated_rows:
                    litres = float(getattr(row, "total_yield", 0.0) or 0.0)
                    row_total += litres
                    if str(getattr(row, "status", "RECORDED") or "RECORDED").upper() == "WITHDRAWAL":
                        row_withdrawal += litres

                if row_total > 0.0 or total == 0.0:
                    total = max(total, row_total)
                withdrawal = row_withdrawal
                saleable = max(total - withdrawal, 0.0)

        return {
            "date": production_date.isoformat(),
            "complete": True,
            "daily_total": total,
            "total_litres": total,
            "saleable_litres": saleable,
            "withdrawal_litres": withdrawal,
        }

    def reconcile(self, production_date: date, *, raise_finding: bool = True):
        repo, owned_factory = self._repo()

        try:
            production_repository = self.production_repository
            if production_repository is None and owned_factory is not None:
                production_repository = owned_factory.milk()

            current = self._production_total(
                production_date,
                production_repository=production_repository,
            )
            dispositions = repo.get_by_date(production_date)

            if not current.get("complete", False):
                return {
                    "production_date": production_date.isoformat(),
                    "production_complete": False,
                    "produced_litres": None,
                    "biological_production_litres": None,
                    "withdrawal_litres": None,
                    "accounted_litres": round(sum(float(item.quantity_litres) for item in dispositions), 3),
                    "sold_litres": round(sum(float(item.quantity_litres) for item in dispositions if str(item.disposition_type).upper() == "SOLD"), 3),
                    "non_sale_accounted_litres": round(sum(float(item.quantity_litres) for item in dispositions if str(item.disposition_type).upper() != "SOLD"), 3),
                    "unaccounted_litres": None,
                    "over_accounted_litres": None,
                    "sale_value": round(sum(float(item.amount_due or 0.0) for item in dispositions if str(item.disposition_type).upper() == "SOLD"), 2),
                    "cash_received": round(sum(float(item.amount_received or 0.0) for item in dispositions if str(item.disposition_type).upper() == "SOLD"), 2),
                    "receivable_outstanding": round(sum(float(item.receivable_outstanding) for item in dispositions if str(item.disposition_type).upper() == "SOLD"), 2),
                    "status": "PRODUCTION_INCOMPLETE",
                    "dispositions": [self._serialize_disposition(item) for item in dispositions],
                }

            produced = float(current["saleable_litres"])
            biological_production = float(current["daily_total"])
            withdrawal_litres = float(current.get("withdrawal_litres") or 0.0)

            accounted = sum(float(item.quantity_litres) for item in dispositions)
            sold = sum(float(item.quantity_litres) for item in dispositions if str(item.disposition_type).upper() == "SOLD")
            non_sale = accounted - sold
            sale_value = sum(float(item.amount_due or 0.0) for item in dispositions if str(item.disposition_type).upper() == "SOLD")
            cash_received = sum(float(item.amount_received or 0.0) for item in dispositions if str(item.disposition_type).upper() == "SOLD")
            receivable = max(sale_value - cash_received, 0.0)

            delta = produced - accounted
            if delta > 0.01:
                status = "UNACCOUNTED_PRODUCTION"
            elif delta < -0.01:
                status = "OVER_ACCOUNTED"
            else:
                status = "RECONCILED"

            result = {
                "production_date": production_date.isoformat(),
                "production_complete": True,
                "produced_litres": round(produced, 3),
                "biological_production_litres": round(biological_production, 3),
                "saleable_litres": round(produced, 3),
                "withdrawal_litres": round(withdrawal_litres, 3),
                "accounted_litres": round(accounted, 3),
                "sold_litres": round(sold, 3),
                "non_sale_accounted_litres": round(non_sale, 3),
                "unaccounted_litres": round(max(delta, 0.0), 3),
                "over_accounted_litres": round(max(-delta, 0.0), 3),
                "sale_value": round(sale_value, 2),
                "cash_received": round(cash_received, 2),
                "receivable_outstanding": round(receivable, 2),
                "status": status,
                "dispositions": [self._serialize_disposition(item) for item in dispositions],
            }

            if raise_finding and status in {"UNACCOUNTED_PRODUCTION", "OVER_ACCOUNTED"}:
                finding_factory = RepositoryFactory.create()
                try:
                    severity = "CRITICAL" if status == "OVER_ACCOUNTED" else "HIGH"
                    MilkFindingService(finding_factory.operational_findings()).raise_or_update(
                        severity=severity,
                        title=f"Milk destination reconciliation exception for {production_date.isoformat()}",
                        detail=(
                            f"Biological production {biological_production:.1f} L; "
                            f"saleable {produced:.1f} L; withdrawal {withdrawal_litres:.1f} L; "
                            f"accounted {accounted:.1f} L; unaccounted {max(delta, 0.0):.1f} L; "
                            f"over-accounted {max(-delta, 0.0):.1f} L."
                        ),
                        subject_type="FARM",
                        subject_id="MILK",
                        route="/farm/milk",
                        dedupe_key=f"MILK_RECONCILIATION:{production_date.isoformat()}",
                    )
                finally:
                    finding_factory.close()

            return result
        finally:
            if owned_factory is not None:
                owned_factory.close()

    @staticmethod
    def _serialize_disposition(item):
        return {
            "id": item.id,
            "disposition_type": item.disposition_type,
            "quantity_litres": item.quantity_litres,
            "sale_id": item.sale_id,
            "counterparty": item.counterparty,
            "selling_price_per_litre": item.selling_price_per_litre,
            "amount_due": item.amount_due,
            "amount_received": item.amount_received,
            "receivable_outstanding": item.receivable_outstanding,
            "notes": item.notes,
            "recorded_by": item.recorded_by,
        }

    def record_disposition(
        self,
        *,
        production_date: date,
        disposition_type: str,
        quantity_litres: float,
        sale_id: str | None = None,
        counterparty: str | None = None,
        selling_price_per_litre: float | None = None,
        notes: str | None = None,
        recorded_by: str | None = None,
    ):
        disposition_type = str(disposition_type).strip().upper()
        if disposition_type not in VALID_DISPOSITIONS:
            raise ValueError(f"Unknown milk disposition: {disposition_type}")
        if quantity_litres <= 0:
            raise ValueError("Milk disposition quantity must be greater than zero.")

        if disposition_type == "SOLD":
            if not sale_id:
                raise ValueError("SOLD milk requires a sale_id.")
            if selling_price_per_litre is None or selling_price_per_litre < 0:
                raise ValueError("SOLD milk requires a non-negative selling price per litre.")
        else:
            sale_id = None
            counterparty = None
            selling_price_per_litre = None

        amount_due = (
            float(quantity_litres) * float(selling_price_per_litre)
            if disposition_type == "SOLD"
            else 0.0
        )

        repo, owned_factory = self._repo()
        try:
            production_repository = self.production_repository
            if production_repository is None and owned_factory is not None:
                production_repository = owned_factory.milk()

            production_basis = self._production_total(
                production_date,
                production_repository=production_repository,
            )

            if production_basis.get("complete"):
                produced_litres = float(production_basis["saleable_litres"])
                already_accounted = sum(float(item.quantity_litres) for item in repo.get_by_date(production_date))
                proposed_total = already_accounted + float(quantity_litres)
                if proposed_total > produced_litres + 0.01:
                    raise ValueError(
                        "Milk disposition quantity exceeds available production "
                        f"for {production_date.isoformat()}: already accounted {already_accounted:.3f} L, "
                        f"requested {float(quantity_litres):.3f} L, saleable production {produced_litres:.3f} L."
                    )

            if disposition_type == "SOLD" and repo.get_by_sale_id(sale_id) is not None:
                raise ValueError(f"Sale ID {sale_id} is already recorded.")

            return repo.add(
                MilkDisposition(
                    production_date=production_date,
                    disposition_type=disposition_type,
                    quantity_litres=float(quantity_litres),
                    sale_id=sale_id,
                    counterparty=counterparty,
                    selling_price_per_litre=selling_price_per_litre,
                    amount_due=amount_due,
                    amount_received=0.0,
                    notes=notes,
                    recorded_by=recorded_by,
                )
            )
        finally:
            if owned_factory is not None:
                owned_factory.close()
