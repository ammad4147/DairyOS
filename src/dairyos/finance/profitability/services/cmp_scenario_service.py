from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from dairyos.finance.profitability.services.cost_of_production_service import (
    CostOfProductionService,
)


class CMPScenarioService:
    """Create and evaluate persisted CMP analytical scenarios."""

    def __init__(self, repository_factory):
        self.factory = repository_factory
        self.cost_service = CostOfProductionService()

    @staticmethod
    def _period_datetimes(
        period_start: date,
        period_end: date,
    ):
        start = datetime.combine(
            period_start,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )
        end = datetime.combine(
            period_end + timedelta(days=1),
            datetime.min.time(),
            tzinfo=timezone.utc,
        )
        return start, end

    @staticmethod
    def _domain_amounts(
        actual: dict,
    ) -> dict[str, float]:
        return {
            key: float(value or 0.0)
            for key, value in actual.get(
                "cost_domain_amounts",
                {},
            ).items()
        }

    @staticmethod
    def _validate_assumptions(
        assumptions: dict,
    ) -> None:
        if not isinstance(assumptions, dict):
            raise ValueError("assumptions must be an object")

        multipliers = assumptions.get(
            "cost_multipliers",
            {},
        )

        additions = assumptions.get(
            "additional_costs",
            {},
        )

        exclusions = assumptions.get(
            "excluded_cost_domains",
            [],
        )

        if not isinstance(multipliers, dict):
            raise ValueError(
                "cost_multipliers must be an object"
            )

        if not isinstance(additions, dict):
            raise ValueError(
                "additional_costs must be an object"
            )

        if not isinstance(exclusions, list):
            raise ValueError(
                "excluded_cost_domains must be a list"
            )

        for domain, multiplier in multipliers.items():
            if float(multiplier) < 0:
                raise ValueError(
                    f"negative cost multiplier for {domain}"
                )

        for domain, amount in additions.items():
            if float(amount) < 0:
                raise ValueError(
                    f"negative additional cost for {domain}"
                )

    def evaluate(
        self,
        *,
        period_start: date,
        period_end: date,
        selected_cost_domains: list[str],
        assumptions: dict,
    ) -> dict:
        self._validate_assumptions(assumptions)

        if period_end < period_start:
            raise ValueError(
                "period_end cannot precede period_start"
            )

        start, end = self._period_datetimes(
            period_start,
            period_end,
        )

        milk_records = self.factory.milk().get_all()
        financial_records = self.factory.finance().get_all()

        milk_records = [
            row for row in milk_records
            if row.production_date is not None
            and start <= self.cost_service._as_utc(
                row.production_date
            ) < end
        ]

        financial_records = [
            row for row in financial_records
            if row.transaction_date is not None
            and start <= self.cost_service._as_utc(
                row.transaction_date
            ) < end
        ]

        actual = self.cost_service.evaluate(
            milk_records,
            financial_records,
            days=(period_end - period_start).days + 1,
            now=end,
        )

        base_domains = self._domain_amounts(actual)

        selected = {
            str(domain).strip().upper()
            for domain in selected_cost_domains
        }

        unknown = selected.difference(
            base_domains
        )

        if unknown:
            raise ValueError(
                "unknown cost domains: "
                + ", ".join(sorted(unknown))
            )

        multipliers = {
            str(key).strip().upper(): float(value)
            for key, value in assumptions.get(
                "cost_multipliers",
                {},
            ).items()
        }

        additions = {
            str(key).strip().upper(): float(value)
            for key, value in assumptions.get(
                "additional_costs",
                {},
            ).items()
        }

        excluded = {
            str(value).strip().upper()
            for value in assumptions.get(
                "excluded_cost_domains",
                [],
            )
        }

        eligible_cost = 0.0

        for domain in sorted(selected):
            if domain in excluded:
                continue

            base = base_domains.get(
                domain,
                0.0,
            )

            adjusted = (
                base
                * multipliers.get(domain, 1.0)
            )

            adjusted += additions.get(
                domain,
                0.0,
            )

            eligible_cost += adjusted

        milk_volume = actual.get(
            "milk_litres"
        )

        cmp_per_litre = (
            round(
                eligible_cost / milk_volume,
                4,
            )
            if milk_volume and milk_volume > 0.001
            else None
        )

        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "currency": "PKR",
            "basis": "PERSISTED_ACTUALS_PLUS_SCENARIO_ASSUMPTIONS",
            "selected_cost_domains": sorted(selected),
            "assumptions": assumptions,
            "actual": {
                "milk_volume_litres": milk_volume,
                "cost_domain_amounts": base_domains,
                "recorded_total_operating_expense": actual.get(
                    "total_recorded_operating_expense"
                ),
                "actual_cost_per_litre": actual.get(
                    "cost_per_litre"
                ),
                "cost_data_completeness": actual.get(
                    "cost_data_completeness"
                ),
            },
            "scenario": {
                "eligible_cost": round(
                    eligible_cost,
                    2,
                ),
                "milk_volume_litres": milk_volume,
                "cmp_per_litre": cmp_per_litre,
            },
            "mutates_authoritative_records": False,
        }

    def create(
        self,
        *,
        name: str,
        created_by: str,
        period_start: date,
        period_end: date,
        selected_cost_domains: list[str],
        assumptions: dict,
    ):
        evaluation = self.evaluate(
            period_start=period_start,
            period_end=period_end,
            selected_cost_domains=selected_cost_domains,
            assumptions=assumptions,
        )

        from dairyos.data.models.cmp_scenario import CMPScenario

        row = CMPScenario(
            scenario_id=(
                "CMP-"
                + uuid4().hex[:12].upper()
            ),
            name=name,
            created_at=datetime.now(
                timezone.utc
            ).replace(
                tzinfo=None
            ),
            created_by=created_by,
            period_start=period_start,
            period_end=period_end,
            currency=evaluation["currency"],
            basis=evaluation["basis"],
            selected_cost_domains=evaluation[
                "selected_cost_domains"
            ],
            assumptions=evaluation[
                "assumptions"
            ],
            milk_volume_litres=evaluation[
                "scenario"
            ]["milk_volume_litres"],
            eligible_cost=evaluation[
                "scenario"
            ]["eligible_cost"],
            cmp_per_litre=evaluation[
                "scenario"
            ]["cmp_per_litre"],
            status="ACTIVE",
        )

        self.factory.session.add(row)
        self.factory.session.commit()
        self.factory.session.refresh(row)

        return row, evaluation

    def list(self):
        return self.factory.cmp_scenarios().get_all()

    def get(self, scenario_id: str):
        return self.factory.cmp_scenarios().get_by_scenario_id(
            scenario_id
        )
