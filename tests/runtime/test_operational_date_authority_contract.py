from datetime import datetime
from zoneinfo import ZoneInfo

from dairyos.farm.settings.services.farm_settings_service import (
    FarmSettingsService,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


class FakeSettings:
    def __init__(self, timezone_name="Asia/Karachi"):
        self.timezone_name = timezone_name

    def get(self, key, default=None):
        if key == "timezone":
            return self.timezone_name
        return default


def test_default_operational_datetime_follows_windows_local_timezone():
    service = FarmSettingsService(FakeSettings(None))

    value = service.get_operational_datetime()
    host_value = datetime.now().astimezone()

    assert service.get_timezone() == "SYSTEM"
    assert value.tzinfo is not None
    assert value.utcoffset() == host_value.utcoffset()


def test_operational_datetime_is_timezone_aware():
    service = FarmSettingsService(
        FakeSettings("Asia/Karachi")
    )

    value = service.get_operational_datetime()

    assert value.tzinfo is not None
    assert str(value.tzinfo) == "Asia/Karachi"


def test_operational_date_comes_from_farm_local_datetime(monkeypatch):
    service = FarmSettingsService(
        FakeSettings("Asia/Karachi")
    )

    farm_time = datetime(
        2026,
        9,
        10,
        0,
        5,
        tzinfo=ZoneInfo("Asia/Karachi"),
    )

    monkeypatch.setattr(
        service,
        "get_operational_datetime",
        lambda: farm_time,
    )

    assert service.get_operational_date().isoformat() == "2026-09-10"


def test_operational_authority_exposes_same_farm_timezone():
    service = FarmSettingsService(
        FakeSettings("Asia/Karachi")
    )

    authority = OperationalDateAuthority(
        settings_service=service,
    )

    value = authority.current_datetime()

    assert value.tzinfo is not None
    assert str(value.tzinfo) == "Asia/Karachi"
