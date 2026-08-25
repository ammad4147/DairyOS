from __future__ import annotations

import logging
import threading
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from dairyos.core.time_utils import utcnow
from dairyos.data.repositories.repository_factory import RepositoryFactory
from .digest import DashboardDigestService, expected_digest_date

log = logging.getLogger(__name__)
LOCAL_ZONE = ZoneInfo("Asia/Karachi")
_LAST_STARTUP_KEY = "email_scheduler_last_startup_utc"


class NightlyEmailScheduler:
    """Lifecycle-owned scheduler for the single DairyOS farm instance."""

    def __init__(self, *, container, interval_seconds: int = 30):
        self.container = container
        self.interval_seconds = max(5, int(interval_seconds))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_attempted_slot: str | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        previous = self._previous_startup()
        current = utcnow()
        self._record_startup(current)
        self._stop.clear()
        self._run_catch_up(previous, current)
        self._thread = threading.Thread(target=self._loop, name="dairyos-email-scheduler", daemon=True)
        self._thread.start()
        log.info("Nightly email scheduler started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None

    def _previous_startup(self) -> datetime | None:
        factory = RepositoryFactory.create()
        try:
            value = factory.app_settings().get(_LAST_STARTUP_KEY)
        finally:
            factory.close()
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value))
            return parsed.replace(tzinfo=ZoneInfo("UTC")) if parsed.tzinfo is None else parsed
        except ValueError:
            return None

    def _record_startup(self, when: datetime) -> None:
        factory = RepositoryFactory.create()
        try:
            factory.app_settings().set(_LAST_STARTUP_KEY, when.isoformat(), updated_by="EMAIL_SCHEDULER")
        finally:
            factory.close()

    def _loop(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            now = datetime.now(LOCAL_ZONE)
            if now.hour == 23 and now.minute == 0:
                slot = now.date().isoformat()
                if slot != self._last_attempted_slot:
                    self._last_attempted_slot = slot
                    self._send(now.date())

    def _run_catch_up(self, previous: datetime | None, current: datetime) -> None:
        if previous is None:
            return
        current_local = current.astimezone(LOCAL_ZONE)
        previous_local = previous.astimezone(LOCAL_ZONE)
        digest_date = expected_digest_date(current_local)
        expected_slot = datetime.combine(digest_date, time(23, 0), tzinfo=LOCAL_ZONE)
        if previous_local.date() == digest_date and previous_local.time() < time(23, 0) and current_local >= expected_slot:
            self._send(digest_date)

    def _send(self, digest_date) -> None:
        try:
            result = DashboardDigestService(container=self.container).send_for_date(digest_date)
            log.info("DairyOS nightly digest result: %s", result)
        except Exception:
            log.exception("DairyOS nightly digest failed for %s", digest_date)
