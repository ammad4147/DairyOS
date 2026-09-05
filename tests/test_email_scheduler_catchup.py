from datetime import datetime
from zoneinfo import ZoneInfo

from dairyos.email.scheduler import NightlyEmailScheduler


class _Scheduler(NightlyEmailScheduler):
    def __init__(self):
        self.sent = []
        self.container = object()
        self.interval_seconds = 30
        import threading
        self._stop = threading.Event()
        self._thread = None
        self._last_attempted_slot = None

    def _zone(self):
        return ZoneInfo("Asia/Karachi")

    def _send(self, digest_date):
        self.sent.append(digest_date)


def test_first_deployed_start_after_slot_catches_up():
    scheduler = _Scheduler()
    current = datetime(2026, 9, 6, 0, 44, tzinfo=ZoneInfo("Asia/Karachi")).astimezone(ZoneInfo("UTC"))
    scheduler._run_catch_up(None, current)
    assert [d.isoformat() for d in scheduler.sent] == ["2026-09-05"]


def test_start_before_slot_does_not_catch_up():
    scheduler = _Scheduler()
    current = datetime(2026, 9, 5, 22, 30, tzinfo=ZoneInfo("Asia/Karachi")).astimezone(ZoneInfo("UTC"))
    scheduler._run_catch_up(None, current)
    assert scheduler.sent == []
