import pytest

from dairyos.intelligence.feed.services.feed_optimization_service import (
    FeedEfficiencyBenchmark,
    FeedOptimizationService,
)


@pytest.fixture
def service() -> FeedOptimizationService:
    return FeedOptimizationService()


def test_ecm_accounts_for_fat_and_protein(service: FeedOptimizationService) -> None:
    ecm = service.calculate_ecm(
        milk_l=30.0,
        fat_pct=4.0,
        protein_pct=3.2,
    )

    assert ecm > 30.0
    assert ecm == pytest.approx(33.23, rel=0.01)


def test_fce_uses_dmi_not_fresh_feed(service: FeedOptimizationService) -> None:
    result = service.evaluate(
        "MILKING",
        dmi_kg=25.0,
        ecm_kg=30.0,
        dim=120,
    )

    assert result.efficiency == pytest.approx(1.20)
    assert result.dmi_kg == 25.0
    assert result.ecm_kg == 30.0
    assert result.status == "ATTENTION"


def test_stage_aware_benchmark_prevents_one_static_cutoff(service: FeedOptimizationService) -> None:
    early = service.evaluate("EARLY", dmi_kg=25, ecm_kg=34, dim=14)
    late = service.evaluate("LATE", dmi_kg=25, ecm_kg=34, dim=250)

    assert early.benchmark_good == 1.50
    assert late.benchmark_good == 1.30
    assert early.status == "ATTENTION"
    assert late.status == "GOOD"


def test_custom_benchmark_overrides_default(service: FeedOptimizationService) -> None:
    result = service.evaluate(
        "CUSTOM",
        dmi_kg=25,
        ecm_kg=32.5,
        dim=150,
        benchmark=FeedEfficiencyBenchmark(good=1.35, attention=1.20),
    )

    assert result.efficiency == pytest.approx(1.30)
    assert result.status == "ATTENTION"
    assert result.benchmark_good == 1.35


def test_legacy_positional_contract_remains_usable(service: FeedOptimizationService) -> None:
    result = service.evaluate("LEGACY", 25.0, 30.0)

    assert result.feed_quantity == 25.0
    assert result.milk_output == 30.0
    assert result.efficiency == pytest.approx(1.20)


def test_invalid_inputs_are_rejected(service: FeedOptimizationService) -> None:
    with pytest.raises(ValueError):
        service.evaluate("X", dmi_kg=-1, ecm_kg=30)

    with pytest.raises(ValueError):
        service.calculate_ecm(30, fat_pct=4, protein_pct=3.2, milk_density_kg_per_l=0)
