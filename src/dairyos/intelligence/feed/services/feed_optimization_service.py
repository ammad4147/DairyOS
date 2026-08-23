from __future__ import annotations

from dataclasses import dataclass

from ..models.feed_efficiency import FeedEfficiency


@dataclass(frozen=True)
class FeedEfficiencyBenchmark:
    """Contextual ECM/DMI thresholds for operational interpretation."""

    good: float
    attention: float

    def __post_init__(self) -> None:
        if self.attention < 0 or self.good < 0:
            raise ValueError("Feed-efficiency thresholds must be non-negative")
        if self.attention > self.good:
            raise ValueError("attention threshold cannot exceed good threshold")


class FeedOptimizationService:
    """Calculate and interpret dairy feed efficiency without changing the UI.

    Feed efficiency is ECM/DMI. ``feed_quantity`` and ``milk_output`` remain
    accepted for backward compatibility, but are interpreted as DMI (kg DM)
    and ECM (kg ECM) rather than fresh feed and raw milk litres.
    """

    DEFAULT_BENCHMARK = FeedEfficiencyBenchmark(good=1.40, attention=1.20)

    @staticmethod
    def benchmark_for_dim(dim: int | None) -> FeedEfficiencyBenchmark:
        """Return a stage-aware default benchmark.

        These are operational reference bands, not immutable biological laws.
        Farm-specific benchmarks can be supplied to ``evaluate``.
        """
        if dim is None:
            return FeedOptimizationService.DEFAULT_BENCHMARK
        if dim < 21:
            return FeedEfficiencyBenchmark(good=1.50, attention=1.30)
        if dim <= 100:
            return FeedEfficiencyBenchmark(good=1.50, attention=1.30)
        if dim <= 200:
            return FeedEfficiencyBenchmark(good=1.40, attention=1.20)
        return FeedEfficiencyBenchmark(good=1.30, attention=1.10)

    @staticmethod
    def calculate_ecm(
        milk_l: float,
        fat_pct: float,
        protein_pct: float,
        *,
        milk_density_kg_per_l: float = 1.03,
    ) -> float:
        """Calculate Energy Corrected Milk (kg ECM/day).

        Tyrrell/Reid-style ECM:
            ECM = 0.327*milk_kg + 12.95*fat_kg + 7.2*protein_kg

        DairyOS milk production is recorded in litres, so a configurable
        milk-density conversion is applied before calculating component yield.
        """
        if milk_l < 0:
            raise ValueError("milk_l must be non-negative")
        if not 0 <= fat_pct <= 100:
            raise ValueError("fat_pct must be between 0 and 100")
        if not 0 <= protein_pct <= 100:
            raise ValueError("protein_pct must be between 0 and 100")
        if milk_density_kg_per_l <= 0:
            raise ValueError("milk_density_kg_per_l must be positive")

        milk_kg = milk_l * milk_density_kg_per_l
        fat_kg = milk_kg * fat_pct / 100.0
        protein_kg = milk_kg * protein_pct / 100.0

        return (
            0.327 * milk_kg
            + 12.95 * fat_kg
            + 7.20 * protein_kg
        )

    def evaluate(
        self,
        group_id: str,
        feed_quantity: float | None = None,
        milk_output: float | None = None,
        *,
        dmi_kg: float | None = None,
        ecm_kg: float | None = None,
        dim: int | None = None,
        benchmark: FeedEfficiencyBenchmark | None = None,
    ) -> FeedEfficiency:
        """Evaluate ECM/DMI while retaining the established method contract."""
        if dmi_kg is not None:
            if feed_quantity is not None and feed_quantity != dmi_kg:
                raise ValueError("Provide either feed_quantity or dmi_kg, not both")
            feed_quantity = dmi_kg

        if ecm_kg is not None:
            if milk_output is not None and milk_output != ecm_kg:
                raise ValueError("Provide either milk_output or ecm_kg, not both")
            milk_output = ecm_kg

        if feed_quantity is None or milk_output is None:
            raise ValueError("DMI and ECM are required for feed-efficiency evaluation")
        if feed_quantity < 0:
            raise ValueError("DMI cannot be negative")
        if milk_output < 0:
            raise ValueError("ECM cannot be negative")

        efficiency = milk_output / feed_quantity if feed_quantity > 0 else 0.0
        selected = benchmark or self.benchmark_for_dim(dim)

        if efficiency >= selected.good:
            status = "GOOD"
            recommendation = "Maintain current ration"
        elif efficiency >= selected.attention:
            status = "ATTENTION"
            recommendation = "Review DMI, ration sorting, feed losses, health and lactation stage"
        else:
            status = "POOR"
            recommendation = "Assess ration formulation, DMI, feed losses, health and body-condition trend"

        return FeedEfficiency(
            group_id=group_id,
            feed_quantity=feed_quantity,
            milk_output=milk_output,
            efficiency=efficiency,
            status=status,
            recommendation=recommendation,
            dmi_kg=feed_quantity,
            ecm_kg=milk_output,
            dim=dim,
            benchmark_good=selected.good,
            benchmark_attention=selected.attention,
            data_quality="HIGH" if dim is not None else "MEDIUM",
        )
