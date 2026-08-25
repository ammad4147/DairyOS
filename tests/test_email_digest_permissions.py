from datetime import datetime
from zoneinfo import ZoneInfo

from dairyos.auth.permissions import permissions_from_json
from dairyos.email.digest import expected_digest_date


def test_custom_permissions_override_role_preset():
    permissions = permissions_from_json('["milk.view","milk.create"]', "MANAGER")
    assert permissions == frozenset({"milk.view", "milk.create"})
    assert "finance.view" not in permissions


def test_missing_permissions_json_uses_role_preset():
    permissions = permissions_from_json(None, "MILKER")
    assert "milk.create" in permissions
    assert "finance.view" not in permissions


def test_digest_date_is_today_after_2300():
    local = ZoneInfo("Asia/Karachi")
    now = datetime(2026, 8, 25, 23, 0, tzinfo=local)
    assert expected_digest_date(now) == datetime(2026, 8, 25).date()


def test_digest_date_is_previous_day_before_2300():
    local = ZoneInfo("Asia/Karachi")
    now = datetime(2026, 8, 26, 8, 30, tzinfo=local)
    assert expected_digest_date(now) == datetime(2026, 8, 25).date()
