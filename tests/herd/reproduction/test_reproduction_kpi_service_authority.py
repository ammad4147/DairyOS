from datetime import datetime, timezone
from types import SimpleNamespace

from dairyos.herd.reproduction.services.reproduction_kpi_service import (
    ReproductionKpiService,
)


def _record(record_id, animal_id, event_type, timestamp, result=None):
    return SimpleNamespace(
        record_id=record_id,
        animal_id=animal_id,
        event_type=event_type,
        timestamp=datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc),
        result=result,
    )


def test_conception_rate_excludes_services_without_documented_outcome():
    service = _record("AI-1", "A1", "insemination", "2026-03-01T08:00:00")
    observed_positive = _record("AI-2", "A1", "insemination", "2026-04-01T08:00:00")
    positive_check = _record(
        "PC-2",
        "A1",
        "pregnancy_diagnosis",
        "2026-04-30T08:00:00",
        result="pregnant",
    )

    outcomes = ReproductionKpiService.conception_outcomes(
        [service, observed_positive],
        [positive_check],
    )

    assert outcomes == {"AI-2": True}
    assert ReproductionKpiService.calculate_observed_conception_rate(
        [service, observed_positive],
        [positive_check],
    ) == 100.0


def test_multiple_diagnoses_update_one_service_without_double_counting():
    service = _record("AI-1", "A1", "insemination", "2026-03-01T08:00:00")
    negative = _record(
        "PC-1",
        "A1",
        "pregnancy_diagnosis",
        "2026-04-01T08:00:00",
        result="open",
    )
    positive = _record(
        "PC-2",
        "A1",
        "pregnancy_diagnosis",
        "2026-04-15T08:00:00",
        result="pregnant",
    )

    outcomes = ReproductionKpiService.conception_outcomes(
        [service],
        [negative, positive],
    )

    assert outcomes == {"AI-1": True}
    assert ReproductionKpiService.calculate_observed_conception_rate(
        [service],
        [negative, positive],
    ) == 100.0


def test_pregnancy_diagnosis_cannot_match_another_animal_service():
    service = _record("AI-1", "A1", "insemination", "2026-03-01T08:00:00")
    diagnosis = _record(
        "PC-2",
        "A2",
        "pregnancy_diagnosis",
        "2026-04-01T08:00:00",
        result="pregnant",
    )

    assert ReproductionKpiService.conception_outcomes(
        [service],
        [diagnosis],
    ) == {}
    assert ReproductionKpiService.calculate_observed_conception_rate(
        [service],
        [diagnosis],
    ) is None


def test_undated_service_or_diagnosis_is_not_an_observed_outcome():
    service = SimpleNamespace(
        record_id="AI-1",
        animal_id="A1",
        event_type="insemination",
        timestamp=None,
    )
    diagnosis = _record(
        "PC-1",
        "A1",
        "pregnancy_diagnosis",
        "2026-04-01T08:00:00",
        result="pregnant",
    )

    assert ReproductionKpiService.conception_outcomes(
        [service],
        [diagnosis],
    ) == {}
    assert ReproductionKpiService.calculate_observed_conception_rate(
        [service],
        [diagnosis],
    ) is None
