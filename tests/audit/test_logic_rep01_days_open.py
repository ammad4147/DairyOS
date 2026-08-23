from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from dairyos.api.dairy_kpi import _interval_metrics


def _event(event_type: str, timestamp: str, animal_id: str = "A-001"):
    return SimpleNamespace(
        animal_id=animal_id,
        event_type=event_type,
        timestamp=datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc),
    )


def test_days_open_uses_calving_to_subsequent_service_not_gestation_length():
    breeding = [
        _event("calving", "2026-01-01T08:00:00"),
        _event("insemination", "2026-03-12T08:00:00"),
        _event("calving", "2026-12-25T08:00:00"),
    ]

    result = _interval_metrics(breeding)

    assert result["days_open"] == 70
    assert result["calving_interval_days"] == 358



def test_days_open_does_not_treat_prior_service_before_calving_as_days_open():
    breeding = [
        _event("insemination", "2025-03-12T08:00:00"),
        _event("calving", "2026-01-01T08:00:00"),
    ]

    result = _interval_metrics(breeding)

    assert result["days_open"] is None
    assert result["days_open_observations"] == 0
