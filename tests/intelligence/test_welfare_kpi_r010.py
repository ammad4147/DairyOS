from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from dairyos.intelligence.welfare_kpi_service import WelfareKPIService


def test_welfare_kpis_use_persisted_health_and_treatment_evidence():
    end = datetime(2026, 8, 13, tzinfo=timezone.utc)
    start = end - timedelta(days=30)
    animals = [
        SimpleNamespace(animal_id="AN-1", active=True),
        SimpleNamespace(animal_id="AN-2", active=True),
    ]
    health = [
        SimpleNamespace(animal_id="AN-1", observed_at=end - timedelta(days=2), severity="HIGH"),
    ]
    treatments = [
        SimpleNamespace(animal_id="AN-1", treated_at=end - timedelta(days=1)),
    ]

    result = WelfareKPIService().evaluate(
        animals=animals,
        health_observations=health,
        treatments=treatments,
        start=start,
        end=end,
    )

    assert result["data_status"] == "LIVE_PERSISTED_DATA"
    assert result["kpis"]["morbidity_rate_percent"] == 50.0
    assert result["kpis"]["treatment_rate_percent"] == 50.0
    assert result["kpis"]["mortality_rate_percent"] is None
    assert result["coverage"]["mortality_rate_percent"] is False
    assert result["provenance"] == "PERSISTED_ANIMAL_HEALTH_AND_TREATMENT_RECORDS"
    assert result["health_severity_counts"] == {"HIGH": 1}


def test_welfare_kpis_do_not_invent_metrics_without_evidence():
    end = datetime(2026, 8, 13, tzinfo=timezone.utc)
    result = WelfareKPIService().evaluate(
        animals=[SimpleNamespace(animal_id="AN-1", active=True)],
        health_observations=[],
        treatments=[],
        start=end - timedelta(days=30),
        end=end,
    )

    assert result["data_status"] == "NO_DATA"
    assert result["kpis"]["morbidity_rate_percent"] is None
    assert result["kpis"]["treatment_rate_percent"] is None
    assert result["kpis"]["mortality_rate_percent"] is None
    assert "mortality_rate_percent" in result["unsupported_metrics"]
    assert "lameness_rate_percent" in result["unsupported_metrics"]
    assert "body_condition_score" in result["unsupported_metrics"]
