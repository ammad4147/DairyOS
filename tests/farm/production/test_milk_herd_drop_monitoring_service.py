from datetime import date

from dairyos.farm.production.services.milk_herd_drop_monitoring_service import (
    MilkHerdDailyDropMonitoringService,
)


DAY = date(2026, 8, 17)


class FakeTrendResult(dict):
    def summary(self):
        return dict(self)


def trend_result(
    *,
    comparison_status="COMPARED",
    percentage=-25.0,
    current=75.0,
    prior=100.0,
    prior_date="2026-08-16",
):
    variance_litres = (
        current - prior
        if current is not None and prior is not None
        else None
    )

    return FakeTrendResult(
        {
            "status": "OPERATIONAL",
            "comparison_status": comparison_status,
            "complete": comparison_status == "COMPARED",
            "is_complete": comparison_status == "COMPARED",
            "daily_total": current,
            "total_litres": current,
            "total_yield": current,
            "variance_percentage": percentage,
            "variance_litres": variance_litres,
            "prior_date": prior_date,
            "prior_total_litres": prior,
            "trend_direction": "DECREASING",
            "period_days": 7,
            "trend": {},
            "series": [],
        }
    )


class FakeFindingRepository:
    pass


class FakeFactory:
    def __init__(self):
        self.findings = FakeFindingRepository()
        self.closed = False

    def operational_findings(self):
        return self.findings

    def close(self):
        self.closed = True


def test_no_comparison_does_not_create_finding(monkeypatch):
    factory = FakeFactory()
    calls = []

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.MilkProductionTrendIntelligenceService.generate",
        lambda self, **kwargs: trend_result(
            comparison_status="NO_COMPARISON",
            percentage=None,
            current=None,
            prior=None,
            prior_date=None,
        ),
    )

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.RepositoryFactory.create",
        lambda: factory,
    )

    class FindingService:
        def __init__(self, repository):
            pass

        def raise_or_update(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.MilkFindingService",
        FindingService,
    )

    result = MilkHerdDailyDropMonitoringService().monitor(DAY)

    assert result["comparison_status"] == "NO_COMPARISON"
    assert calls == []


def test_decline_below_ten_percent_does_not_create_finding(monkeypatch):
    factory = FakeFactory()
    calls = []

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.MilkProductionTrendIntelligenceService.generate",
        lambda self, **kwargs: trend_result(
            percentage=-9.9,
            current=90.1,
            prior=100.0,
        ),
    )

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.RepositoryFactory.create",
        lambda: factory,
    )

    class FindingService:
        def __init__(self, repository):
            pass

        def raise_or_update(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.MilkFindingService",
        FindingService,
    )

    result = MilkHerdDailyDropMonitoringService().monitor(DAY)

    assert result["variance_percentage"] == -9.9
    assert calls == []


def test_fifteen_to_twenty_percent_decline_creates_amber_farm_finding(monkeypatch):
    factory = FakeFactory()
    calls = []

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.MilkProductionTrendIntelligenceService.generate",
        lambda self, **kwargs: trend_result(
            percentage=-20.0,
            current=80.0,
            prior=100.0,
        ),
    )

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.RepositoryFactory.create",
        lambda: factory,
    )

    class FindingService:
        def __init__(self, repository):
            assert repository is factory.findings

        def raise_or_update(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.MilkFindingService",
        FindingService,
    )

    result = MilkHerdDailyDropMonitoringService().monitor(DAY)

    assert result["variance_percentage"] == -20.0
    assert len(calls) == 1
    assert calls[0]["severity"] == "AMBER"
    assert calls[0]["subject_type"] == "FARM"
    assert calls[0]["subject_id"] == "MILK"
    assert calls[0]["route"] == "/farm/milk"
    assert calls[0]["dedupe_key"] == "MILK_HERD_DAILY_DROP"
    assert DAY.isoformat() in calls[0]["title"]
    assert "2026-08-16" in calls[0]["detail"]
    assert "100.0 L" in calls[0]["detail"]
    assert "80.0 L" in calls[0]["detail"]
    assert "20.0% decline" in calls[0]["detail"]
    assert factory.closed is True


def test_above_twenty_percent_decline_creates_red_farm_finding(monkeypatch):
    factory = FakeFactory()
    calls = []

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.MilkProductionTrendIntelligenceService.generate",
        lambda self, **kwargs: trend_result(
            percentage=-60.0,
            current=40.0,
            prior=100.0,
        ),
    )

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.RepositoryFactory.create",
        lambda: factory,
    )

    class FindingService:
        def __init__(self, repository):
            pass

        def raise_or_update(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.MilkFindingService",
        FindingService,
    )

    result = MilkHerdDailyDropMonitoringService().monitor(DAY)

    assert result["variance_percentage"] == -60.0
    assert len(calls) == 1
    assert calls[0]["severity"] == "RED"
    assert calls[0]["subject_type"] == "FARM"
    assert calls[0]["subject_id"] == "MILK"
    assert calls[0]["dedupe_key"] == "MILK_HERD_DAILY_DROP"
    assert factory.closed is True


def test_increase_does_not_create_finding(monkeypatch):
    factory = FakeFactory()
    calls = []

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.MilkProductionTrendIntelligenceService.generate",
        lambda self, **kwargs: trend_result(
            percentage=15.0,
            current=115.0,
            prior=100.0,
        ),
    )

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.RepositoryFactory.create",
        lambda: factory,
    )

    class FindingService:
        def __init__(self, repository):
            pass

        def raise_or_update(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.MilkFindingService",
        FindingService,
    )

    result = MilkHerdDailyDropMonitoringService().monitor(DAY)

    assert result["variance_percentage"] == 15.0
    assert calls == []


def test_detector_uses_requested_production_date_and_seven_day_window(monkeypatch):
    captured = {}

    def generate(self, **kwargs):
        captured.update(kwargs)
        return trend_result(
            percentage=-5.0,
            current=88.0,
            prior=100.0,
        )

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.MilkProductionTrendIntelligenceService.generate",
        generate,
    )

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_herd_drop_monitoring_service.RepositoryFactory.create",
        lambda: (_ for _ in ()).throw(
            AssertionError(
                "finding repository must not be opened for this unit test"
            )
        ),
    )

    result = MilkHerdDailyDropMonitoringService().monitor(DAY)

    assert result["comparison_status"] == "COMPARED"
    assert captured["as_of_date"] == DAY
    assert captured["period_days"] == 7

