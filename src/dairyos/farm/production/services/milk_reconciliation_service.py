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

    Reconciliation is deliberately downstream of the milk trend service's
    date-completeness decision.

    The trend service is authoritative for whether the production date is
    complete. A missing/incomplete daily snapshot is never silently treated
    as zero production or as a complete production day.
    """

    def __init__(self, disposition_repository=None):
        self.disposition_repository = disposition_repository

    def _repo(self):
        if self.disposition_repository is not None:
            return self.disposition_repository, None

        factory = RepositoryFactory.create()
        return factory.milk_dispositions(), factory

    @staticmethod
    def _production_total(production_date: date) -> dict:
        """Return an explicit production-date reconciliation basis.

        The previous implementation selected an item from ``snapshot["series"]``
        and then inferred completeness from a missing key. That was unsafe:
        series entries do not carry the current-date completeness contract.

        The trend result itself already exposes:
            - complete
            - daily_total
            - total_litres
            - date/comparison metadata

        Reconciliation consumes that authoritative current-date state directly.
        """

        trend = MilkProductionTrendIntelligenceService()

        snapshot = trend.generate(
            as_of_date=production_date,
            period_days=7,
        ).summary()

        complete = bool(
            snapshot.get(
                "complete",
                snapshot.get("is_complete", False),
            )
        )

        if not complete:
            return {
                "date": production_date.isoformat(),
                "complete": False,
                "daily_total": None,
                "total_litres": None,
            }

        daily_total = snapshot.get("daily_total")

        if daily_total is None:
            daily_total = snapshot.get("total_litres")

        if daily_total is None:
            daily_total = snapshot.get("total_yield")

        if daily_total is None:
            # A result claiming completeness without a production total is
            # internally inconsistent. Treat it conservatively as incomplete
            # rather than inventing zero production.
            return {
                "date": production_date.isoformat(),
                "complete": False,
                "daily_total": None,
                "total_litres": None,
            }

        total = float(daily_total)

        return {
            "date": production_date.isoformat(),
            "complete": True,
            "daily_total": total,
            "total_litres": total,
        }

    def reconcile(
        self,
        production_date: date,
        *,
        raise_finding: bool = True,
    ):
        repo, owned_factory = self._repo()

        try:
            current = self._production_total(production_date)
            dispositions = repo.get_by_date(production_date)

            production_complete = bool(current.get("complete", False))

            if not production_complete:
                return {
                    "production_date": production_date.isoformat(),
                    "production_complete": False,
                    "produced_litres": None,
                    "accounted_litres": round(
                        sum(
                            float(item.quantity_litres)
                            for item in dispositions
                        ),
                        3,
                    ),
                    "sold_litres": round(
                        sum(
                            float(item.quantity_litres)
                            for item in dispositions
                            if str(
                                item.disposition_type
                            ).upper()
                            == "SOLD"
                        ),
                        3,
                    ),
                    "non_sale_accounted_litres": round(
                        sum(
                            float(item.quantity_litres)
                            for item in dispositions
                            if str(
                                item.disposition_type
                            ).upper()
                            != "SOLD"
                        ),
                        3,
                    ),
                    "unaccounted_litres": None,
                    "over_accounted_litres": None,
                    "sale_value": round(
                        sum(
                            float(item.amount_due or 0.0)
                            for item in dispositions
                            if str(
                                item.disposition_type
                            ).upper()
                            == "SOLD"
                        ),
                        2,
                    ),
                    "cash_received": round(
                        sum(
                            float(item.amount_received or 0.0)
                            for item in dispositions
                            if str(
                                item.disposition_type
                            ).upper()
                            == "SOLD"
                        ),
                        2,
                    ),
                    "receivable_outstanding": round(
                        sum(
                            float(item.receivable_outstanding)
                            for item in dispositions
                            if str(
                                item.disposition_type
                            ).upper()
                            == "SOLD"
                        ),
                        2,
                    ),
                    "status": "PRODUCTION_INCOMPLETE",
                    "dispositions": [
                        self._serialize_disposition(item)
                        for item in dispositions
                    ],
                }

            produced = float(
                current["daily_total"]
            )

            accounted = sum(
                float(item.quantity_litres)
                for item in dispositions
            )

            sold = sum(
                float(item.quantity_litres)
                for item in dispositions
                if str(
                    item.disposition_type
                ).upper()
                == "SOLD"
            )

            non_sale = accounted - sold

            sale_value = sum(
                float(item.amount_due or 0.0)
                for item in dispositions
                if str(
                    item.disposition_type
                ).upper()
                == "SOLD"
            )

            cash_received = sum(
                float(item.amount_received or 0.0)
                for item in dispositions
                if str(
                    item.disposition_type
                ).upper()
                == "SOLD"
            )

            receivable = max(
                sale_value - cash_received,
                0.0,
            )

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
                "produced_litres": round(
                    produced,
                    3,
                ),
                "accounted_litres": round(
                    accounted,
                    3,
                ),
                "sold_litres": round(
                    sold,
                    3,
                ),
                "non_sale_accounted_litres": round(
                    non_sale,
                    3,
                ),
                "unaccounted_litres": round(
                    max(delta, 0.0),
                    3,
                ),
                "over_accounted_litres": round(
                    max(-delta, 0.0),
                    3,
                ),
                "sale_value": round(
                    sale_value,
                    2,
                ),
                "cash_received": round(
                    cash_received,
                    2,
                ),
                "receivable_outstanding": round(
                    receivable,
                    2,
                ),
                "status": status,
                "dispositions": [
                    self._serialize_disposition(item)
                    for item in dispositions
                ],
            }

            if (
                raise_finding
                and status
                in {
                    "UNACCOUNTED_PRODUCTION",
                    "OVER_ACCOUNTED",
                }
            ):
                finding_factory = RepositoryFactory.create()

                try:
                    severity = (
                        "CRITICAL"
                        if status == "OVER_ACCOUNTED"
                        else "HIGH"
                    )

                    MilkFindingService(
                        finding_factory.operational_findings()
                    ).raise_or_update(
                        severity=severity,
                        title=(
                            "Milk destination reconciliation exception "
                            f"for {production_date.isoformat()}"
                        ),
                        detail=(
                            f"Produced {produced:.1f} L; "
                            f"accounted {accounted:.1f} L; "
                            f"unaccounted "
                            f"{max(delta, 0.0):.1f} L; "
                            f"over-accounted "
                            f"{max(-delta, 0.0):.1f} L."
                        ),
                        subject_type="FARM",
                        subject_id="MILK",
                        route="/farm/milk",
                        dedupe_key=(
                            "MILK_RECONCILIATION:"
                            f"{production_date.isoformat()}"
                        ),
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
            "selling_price_per_litre": (
                item.selling_price_per_litre
            ),
            "amount_due": item.amount_due,
            "amount_received": item.amount_received,
            "receivable_outstanding": (
                item.receivable_outstanding
            ),
            "notes": item.notes,
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
        disposition_type = (
            str(disposition_type)
            .strip()
            .upper()
        )

        if disposition_type not in VALID_DISPOSITIONS:
            raise ValueError(
                f"Unknown milk disposition: {disposition_type}"
            )

        if quantity_litres <= 0:
            raise ValueError(
                "Milk disposition quantity must be greater than zero."
            )

        if disposition_type == "SOLD":
            if not sale_id:
                raise ValueError(
                    "SOLD milk requires a sale_id."
                )

            if (
                selling_price_per_litre is None
                or selling_price_per_litre < 0
            ):
                raise ValueError(
                    "SOLD milk requires a non-negative "
                    "selling price per litre."
                )
        else:
            sale_id = None
            counterparty = None
            selling_price_per_litre = None

        amount_due = (
            float(quantity_litres)
            * float(selling_price_per_litre)
            if disposition_type == "SOLD"
            else 0.0
        )

        repo, owned_factory = self._repo()

        try:
            if (
                disposition_type == "SOLD"
                and repo.get_by_sale_id(sale_id) is not None
            ):
                raise ValueError(
                    f"Sale ID {sale_id} is already recorded."
                )

            item = MilkDisposition(
                production_date=production_date,
                disposition_type=disposition_type,
                quantity_litres=float(
                    quantity_litres
                ),
                sale_id=sale_id,
                counterparty=counterparty,
                selling_price_per_litre=(
                    selling_price_per_litre
                ),
                amount_due=amount_due,
                amount_received=0.0,
                notes=notes,
                recorded_by=recorded_by,
            )

            return repo.add(item)

        finally:
            if owned_factory is not None:
                owned_factory.close()