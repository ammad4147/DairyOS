from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from dairyos.missed_milking_scheduler import (
    LAST_RECONCILED_DATE_KEY,
    DailyMissedMilkingScheduler,
)


def test_app_lifespan_owns_daily_scheduler():
    app_source = (
        Path(__file__).resolve().parents[2] / "src" / "dairyos" / "app.py"
    ).read_text(encoding="utf-8")

    assert "missed_milking_scheduler.start()" in app_source
    assert "missed_milking_scheduler.stop()" in app_source


class FakeSettingsRepository:
    def __init__(self, last_run=None):
        self.values = {LAST_RECONCILED_DATE_KEY: last_run}
        self.set_calls = []

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value, *, updated_by=None):
        self.values[key] = value
        self.set_calls.append((key, value, updated_by))


def factory_with(settings_repository):
    factory = Mock()
    factory.app_settings.return_value = settings_repository
    return factory


def fixed_now(hour, minute):
    return lambda zone: datetime(2026, 9, 4, hour, minute, tzinfo=zone)


def test_scheduler_runs_once_after_farm_local_midnight():
    settings = FakeSettingsRepository()
    factory = factory_with(settings)
    scheduler = DailyMissedMilkingScheduler(
        factory_provider=lambda: factory,
        now_provider=fixed_now(0, 5),
    )

    with patch(
        "dairyos.missed_milking_scheduler.MissedMilkingControlService"
    ) as service_type:
        service_type.return_value.reconcile.return_value = {"raised": 2}

        assert scheduler._run_if_due() is True
        assert scheduler._run_if_due() is False

    service_type.return_value.reconcile.assert_called_once_with(
        as_of_date=date(2026, 9, 4),
        lookback_days=31,
    )
    assert settings.set_calls == [
        (
            LAST_RECONCILED_DATE_KEY,
            "2026-09-04",
            "MISSED_MILKING_SCHEDULER",
        )
    ]
    assert factory.close.call_count == 2


def test_scheduler_does_not_run_before_daily_time():
    settings = FakeSettingsRepository()
    factory = factory_with(settings)
    scheduler = DailyMissedMilkingScheduler(
        factory_provider=lambda: factory,
        now_provider=fixed_now(0, 4),
    )

    with patch(
        "dairyos.missed_milking_scheduler.MissedMilkingControlService"
    ) as service_type:
        assert scheduler._run_if_due() is False

    service_type.assert_not_called()
    assert settings.set_calls == []


def test_scheduler_uses_configured_farm_timezone():
    settings = FakeSettingsRepository()
    settings.values["timezone"] = "Asia/Karachi"
    factory = factory_with(settings)
    observed = []

    def now_provider(zone):
        observed.append(zone)
        return datetime(2026, 9, 4, 0, 5, tzinfo=zone)

    scheduler = DailyMissedMilkingScheduler(
        factory_provider=lambda: factory,
        now_provider=now_provider,
    )

    with patch("dairyos.missed_milking_scheduler.MissedMilkingControlService"):
        assert scheduler._run_if_due() is True

    assert observed == [ZoneInfo("Asia/Karachi")]


def test_failed_run_is_not_marked_complete_and_can_retry():
    settings = FakeSettingsRepository()
    factory = factory_with(settings)
    scheduler = DailyMissedMilkingScheduler(
        factory_provider=lambda: factory,
        now_provider=fixed_now(0, 5),
    )

    with patch(
        "dairyos.missed_milking_scheduler.MissedMilkingControlService"
    ) as service_type:
        service_type.return_value.reconcile.side_effect = RuntimeError("failed")

        assert scheduler._run_if_due() is False
        assert scheduler._run_if_due() is False

    assert service_type.return_value.reconcile.call_count == 2
    assert settings.set_calls == []
    assert factory.session.rollback.call_count == 2
