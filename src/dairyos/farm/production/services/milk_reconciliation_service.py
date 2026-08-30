from __future__ import annotations

from collections.abc import Callable
from datetime import date

from dairyos.data.models.milk_disposition import MilkDisposition
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
    MilkProductionTrendIntelligenceService,
)
from dairyos.farm.production.services.milk_finding_service import MilkFindingService
from dairyos.farm.settings.services.deployment_control_service import DeploymentControlService
from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService


VALID_DISPOSITIONS = frozenset(
    {
        "SOLD",
        "CALF_FEED",
        "DOMESTIC_USE",
        "WASTAGE",
        "OTHER",
        "WITHDRAWAL",
    }
)


class MilkReconciliationService:
    """Authoritative daily milk production and destination reconciliation."""

    def __init__(
        self,
        disposition_repository=None,
        production_repository=None,
        deployment_checker: Callable[[], bool] | None = None,
    ):
        self.disposition_repository = disposition_repository
        self.production_repository = production_repository
        self.deployment_checker = deployment_checker

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

        if isinstance(value, date):
            return value

        try:
            return date.fromisoformat(str(value)[:10])
        except (TypeError, ValueError):
            return None

    @classmethod
    def _dated_production_rows(
        cls,
        production_date: date,
        production_repository,
    ):
        """Return persisted non-void production rows for one operational date.

        Prefer a repository date-specific query when available. Fall back to
        get_all() for lightweight and test repository implementations.
        """
        if production_repository is None:
            return []

        getter = getattr(
            production_repository,
            "get_by_date",
            None,
        )

        if getter is not None:
            rows = list(
                getter(production_date) or []
            )
        else:
            all_getter = getattr(
                production_repository,
                "get_all",
                None,
            )

            if all_getter is None:
                return []

            rows = [
                row
                for row in (all_getter() or [])
                if cls._as_production_date(
                    getattr(
                        row,
                        "production_date",
                        None,
                    )
                ) == production_date
            ]

        return [
            row
            for row in rows
            if str(
                getattr(
                    row,
                    "status",
                    "RECORDED",
                )
                or "RECORDED"
            ).upper()
            != "VOID"
        ]

    @classmethod
    def _persisted_production_total(
        cls,
        production_date: date,
        production_repository,
    ) -> tuple[float, float, bool]:
        """Return (known litres, withdrawal litres, has_rows)."""

        rows = cls._dated_production_rows(
            production_date,
            production_repository,
        )

        total = 0.0
        withdrawal = 0.0

        for row in rows:
            value = getattr(row, "total_yield", None)

            if value is None:
                values = (
                    getattr(row, "morning_yield", None),
                    getattr(row, "afternoon_yield", None),
                    getattr(row, "evening_yield", None),
                )
                value = sum(
                    float(item)
                    for item in values
                    if item is not None
                )

            litres = float(value or 0.0)
            total += litres

            if (
                str(
                    getattr(row, "status", "RECORDED")
                    or "RECORDED"
                ).upper()
                == "WITHDRAWAL"
            ):
                withdrawal += litres

        return (
            round(total, 3),
            round(max(withdrawal, 0.0), 3),
            bool(rows),
        )

    @classmethod
    def _production_total(
        cls,
        production_date: date,
        production_repository=None,
    ) -> dict:
        """Build the authoritative production basis.

        Important contract:

        * Persisted production rows determine litres known for the date.
        * Trend intelligence determines operational completeness.
        * Incomplete does not mean unknown.
        * Known production must remain available to reconciliation and
          disposition validation even while additional expected sessions
          remain outstanding.
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

        persisted_total, persisted_withdrawal, has_rows = (
            cls._persisted_production_total(
                production_date,
                production_repository,
            )
        )

        snapshot_daily_total = snapshot.get("daily_total")

        if snapshot_daily_total is None:
            snapshot_daily_total = snapshot.get("total_litres")

        if snapshot_daily_total is None:
            snapshot_daily_total = snapshot.get("total_yield")

        # No persisted rows plus no snapshot total means production is
        # genuinely unknown. Preserve None rather than converting unknown
        # production into zero.
        snapshot_total = (
            float(snapshot_daily_total)
            if snapshot_daily_total is not None
            else None
        )

        # Persisted ledger rows are authoritative whenever present.
        # Snapshot values are only a fallback when no persisted rows exist.
        total = (
            persisted_total
            if has_rows
            else snapshot_total
        )

        if total is None:
            withdrawal = None
            saleable = None
        else:
            withdrawal = min(
                persisted_withdrawal,
                max(total, 0.0),
            )
            saleable = max(
                total - withdrawal,
                0.0,
            )

        return {
            "date": production_date.isoformat(),
            "complete": complete,
            "has_persisted_rows": has_rows,
            "daily_total": (
                round(total, 3)
                if total is not None
                else None
            ),
            "total_litres": (
                round(total, 3)
                if total is not None
                else None
            ),
            "saleable_litres": (
                round(saleable, 3)
                if saleable is not None
                else None
            ),
            "withdrawal_litres": (
                round(withdrawal, 3)
                if withdrawal is not None
                else None
            ),
        }

    @staticmethod
    def _active_disposition_sum(
        dispositions,
        disposition_type_filter=None,
    ):
        return sum(
            float(item.quantity_litres or 0.0)
            for item in dispositions
            if str(
                getattr(item, "status", "RECORDED")
                or "RECORDED"
            ).upper()
            != "VOID"
            and (
                disposition_type_filter is None
                or str(item.disposition_type).upper()
                == disposition_type_filter
            )
        )

    @classmethod
    def validate_disposition_quantity(
        cls,
        *,
        production_basis: dict,
        dispositions,
        disposition_type: str,
        quantity_litres: float,
        exclude_id: int | None = None,
    ) -> None:
        disposition_type = str(
            disposition_type
        ).strip().upper()

        if quantity_litres <= 0:
            raise ValueError(
                "Milk disposition quantity must be greater than zero."
            )

        # There is no available production to validate against only when
        # production is genuinely absent. An operationally incomplete day
        # can still contain valid known production and must remain usable.
        saleable_raw = production_basis.get("saleable_litres")

        if saleable_raw is None:
            return

        active = [
            item
            for item in dispositions
            if str(
                getattr(item, "status", "RECORDED")
                or "RECORDED"
            ).upper()
            != "VOID"
            and (
                exclude_id is None
                or getattr(item, "id", None) != exclude_id
            )
        ]

        if disposition_type == "WITHDRAWAL":
            available = max(
                float(
                    production_basis.get(
                        "withdrawal_litres"
                    )
                    or 0.0
                )
                - cls._active_disposition_sum(
                    active,
                    "WITHDRAWAL",
                ),
                0.0,
            )

            if float(quantity_litres) > available + 0.01:
                raise ValueError(
                    "WITHDRAWAL milk disposition exceeds recorded "
                    "withdrawal litres: "
                    f"available {available:.3f} L, "
                    f"requested {float(quantity_litres):.3f} L."
                )

            return

        ordinary_active = sum(
            float(item.quantity_litres or 0.0)
            for item in active
            if str(item.disposition_type).upper()
            != "WITHDRAWAL"
        )

        available = max(
            float(saleable_raw or 0.0)
            - ordinary_active,
            0.0,
        )

        if float(quantity_litres) > available + 0.01:
            raise ValueError(
                "Milk disposition quantity exceeds available "
                "saleable production: "
                f"already accounted {ordinary_active:.3f} L, "
                f"requested {float(quantity_litres):.3f} L, "
                f"saleable production "
                f"{float(saleable_raw):.3f} L."
            )

    def _is_deployed_for_findings(self) -> bool:
        if self.deployment_checker is not None:
            return bool(self.deployment_checker())

        if self.disposition_repository is not None:
            factory = getattr(
                self.disposition_repository,
                "factory",
                None,
            )
            if factory is None:
                return True

        factory = RepositoryFactory.create()

        try:
            return DeploymentControlService(
                FarmSettingsService(
                    factory.app_settings()
                )
            ).is_deployed()
        finally:
            factory.close()

    @staticmethod
    def _serialized_dispositions(dispositions):
        return [
            MilkReconciliationService._serialize_disposition(
                item
            )
            for item in dispositions
        ]

    def reconcile(
        self,
        production_date: date,
        *,
        raise_finding: bool = True,
    ):
        repo, owned_factory = self._repo()

        try:
            production_repository = self.production_repository

            if (
                production_repository is None
                and owned_factory is not None
            ):
                production_repository = owned_factory.milk()

            current = self._production_total(
                production_date,
                production_repository=production_repository,
            )

            dispositions = repo.get_by_date(
                production_date
            )

            active = [
                item
                for item in dispositions
                if str(
                    getattr(
                        item,
                        "status",
                        "RECORDED",
                    )
                    or "RECORDED"
                ).upper()
                != "VOID"
            ]

            produced = (
                float(
                    current.get("saleable_litres")
                    or 0.0
                )
                if current.get("has_persisted_rows")
                or current.get("total_litres")
                is not None
                else None
            )

            biological_production = (
                float(
                    current.get("daily_total")
                    or 0.0
                )
                if current.get("has_persisted_rows")
                or current.get("total_litres")
                is not None
                else None
            )

            withdrawal_litres = float(
                current.get(
                    "withdrawal_litres"
                )
                or 0.0
            )

            sold = sum(
                float(item.quantity_litres or 0.0)
                for item in active
                if str(
                    item.disposition_type
                ).upper()
                == "SOLD"
            )

            non_sale = sum(
                float(item.quantity_litres or 0.0)
                for item in active
                if str(
                    item.disposition_type
                ).upper()
                not in {
                    "SOLD",
                    "WITHDRAWAL",
                }
            )

            withdrawal_accounted = sum(
                float(item.quantity_litres or 0.0)
                for item in active
                if str(
                    item.disposition_type
                ).upper()
                == "WITHDRAWAL"
            )

            ordinary_accounted = sold + non_sale

            accounted = (
                ordinary_accounted
                + withdrawal_accounted
            )

            sale_value = sum(
                float(item.amount_due or 0.0)
                for item in active
                if str(
                    item.disposition_type
                ).upper()
                == "SOLD"
            )

            cash_received = sum(
                float(item.amount_received or 0.0)
                for item in active
                if str(
                    item.disposition_type
                ).upper()
                == "SOLD"
            )

            receivable = max(
                sale_value - cash_received,
                0.0,
            )

            # Without known production there is nothing to reconcile.
            if produced is None:
                return {
                    "production_date":
                        production_date.isoformat(),
                    "production_complete": False,
                    "produced_litres": None,
                    "biological_production_litres":
                        None,
                    "saleable_litres": None,
                    "withdrawal_litres":
                        None,
                    "withdrawal_accounted_litres":
                        round(
                            withdrawal_accounted,
                            3,
                        ),
                    "accounted_litres":
                        round(accounted, 3),
                    "sold_litres":
                        round(sold, 3),
                    "non_sale_accounted_litres":
                        round(non_sale, 3),
                    "unaccounted_litres":
                        None,
                    "over_accounted_litres":
                        None,
                    "unaccounted_saleable_litres":
                        None,
                    "unaccounted_withdrawal_litres":
                        None,
                    "sale_value":
                        round(sale_value, 2),
                    "cash_received":
                        round(cash_received, 2),
                    "receivable_outstanding":
                        round(receivable, 2),
                    "status":
                        "PRODUCTION_INCOMPLETE",
                    "dispositions":
                        self._serialized_dispositions(
                            dispositions
                        ),
                }

            saleable_delta = (
                float(produced)
                - ordinary_accounted
            )

            withdrawal_delta = (
                withdrawal_litres
                - withdrawal_accounted
            )

            delta = (
                saleable_delta
                + withdrawal_delta
            )

            if (
                not current["complete"]
            ):
                status = "PRODUCTION_INCOMPLETE"
            elif (
                saleable_delta > 0.01
                or withdrawal_delta > 0.01
            ):
                status = "UNACCOUNTED_PRODUCTION"
            elif (
                saleable_delta < -0.01
                or withdrawal_delta < -0.01
            ):
                status = "OVER_ACCOUNTED"
            else:
                status = "RECONCILED"

            result = {
                "production_date":
                    production_date.isoformat(),
                "production_complete":
                    bool(current["complete"]),
                "produced_litres":
                    round(produced, 3),
                "biological_production_litres":
                    round(
                        biological_production,
                        3,
                    ),
                "saleable_litres":
                    round(produced, 3),
                "withdrawal_litres":
                    round(
                        withdrawal_litres,
                        3,
                    ),
                "withdrawal_accounted_litres":
                    round(
                        withdrawal_accounted,
                        3,
                    ),
                "accounted_litres":
                    round(accounted, 3),
                "sold_litres":
                    round(sold, 3),
                "non_sale_accounted_litres":
                    round(non_sale, 3),
                "unaccounted_litres":
                    round(
                        max(delta, 0.0),
                        3,
                    ),
                "over_accounted_litres":
                    round(
                        max(-delta, 0.0),
                        3,
                    ),
                "unaccounted_saleable_litres":
                    round(
                        max(
                            saleable_delta,
                            0.0,
                        ),
                        3,
                    ),
                "unaccounted_withdrawal_litres":
                    round(
                        max(
                            withdrawal_delta,
                            0.0,
                        ),
                        3,
                    ),
                "sale_value":
                    round(sale_value, 2),
                "cash_received":
                    round(cash_received, 2),
                "receivable_outstanding":
                    round(receivable, 2),
                "status": status,
                "dispositions":
                    self._serialized_dispositions(
                        dispositions
                    ),
            }

            if (
                raise_finding
                and status
                in {
                    "UNACCOUNTED_PRODUCTION",
                    "OVER_ACCOUNTED",
                }
                and self._is_deployed_for_findings()
            ):
                finding_factory = (
                    RepositoryFactory.create()
                )

                try:
                    severity = (
                        "CRITICAL"
                        if status
                        == "OVER_ACCOUNTED"
                        else "HIGH"
                    )

                    MilkFindingService(
                        finding_factory.operational_findings()
                    ).raise_or_update(
                        severity=severity,
                        title=(
                            "Milk destination "
                            "reconciliation "
                            f"exception for "
                            f"{production_date.isoformat()}"
                        ),
                        detail=(
                            "Biological production "
                            f"{biological_production:.1f} L; "
                            "saleable "
                            f"{produced:.1f} L; "
                            "withdrawal "
                            f"{withdrawal_litres:.1f} L; "
                            "ordinary accounted "
                            f"{ordinary_accounted:.1f} L; "
                            "withdrawal accounted "
                            f"{withdrawal_accounted:.1f} L; "
                            "unaccounted saleable "
                            f"{max(saleable_delta, 0.0):.1f} L; "
                            "unaccounted withdrawal "
                            f"{max(withdrawal_delta, 0.0):.1f} L."
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
            "disposition_type":
                item.disposition_type,
            "quantity_litres":
                item.quantity_litres,
            "sale_id": item.sale_id,
            "counterparty":
                item.counterparty,
            "selling_price_per_litre":
                item.selling_price_per_litre,
            "amount_due":
                item.amount_due,
            "amount_received":
                item.amount_received,
            "receivable_outstanding":
                item.receivable_outstanding,
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
        disposition_type = str(
            disposition_type
        ).strip().upper()

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
            # Sale metadata belongs exclusively to SOLD milk.
            sale_id = None
            counterparty = None
            selling_price_per_litre = None

        repo, owned_factory = self._repo()

        try:
            if sale_id and repo.get_by_sale_id(sale_id) is not None:
                raise ValueError(
                    f"Milk sale_id {sale_id} is already recorded."
                )

            production_basis = self._production_total(
                production_date,
                production_repository=self.production_repository,
            )

            existing = repo.get_by_date(
                production_date
            )

            # Validate every disposition against the authoritative production
            # basis. When an explicit production repository is injected, the
            # persisted production rows are used. Otherwise the trend service
            # supplies the production basis through its normal data boundary.
            #
            # A genuinely unknown/incomplete production basis carries
            # saleable_litres=None and is deliberately not treated as zero.
            self.validate_disposition_quantity(
                production_basis=production_basis,
                dispositions=existing,
                disposition_type=disposition_type,
                quantity_litres=float(quantity_litres),
            )

            amount_due = (
                float(quantity_litres)
                * float(selling_price_per_litre)
                if disposition_type == "SOLD"
                else 0.0
            )

            disposition = MilkDisposition(
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

            repo.add(disposition)

            if getattr(repo, "session", None) is not None:
                repo.session.commit()
                repo.session.refresh(disposition)

            return disposition

        finally:
            if owned_factory is not None:
                owned_factory.close()
