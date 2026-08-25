from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from .digest import DashboardDigestService, expected_digest_date

log = logging.getLogger(__name__)


class NightlyEmailScheduler:
    """Small lifecycle-owned scheduler for the single Windows farm instance."""

    def __init__(self, *, container, interval_seconds: int = 30):
        self.container = container
        self.interval_seconds = max(5, int(interval_seconds))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_attempted_slot: str | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._run_catch_up()
        self._thread = threading.Thread(target=self._loop, name="dairyos-email-scheduler", daemon=True)
        self._thread.start()
        log.info("Nightly email scheduler started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None

    def _loop(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            now = datetime.now(ZoneInfo("Asia/Karachi"))
            if now.hour == 23 and now.minute == 0:
                slot = now.date().isoformat()
                if slot != self._last_attempted_slot:
                    self._last_attempted_slot = slot
                    self._send(now.date())

    def _run_catch_up(self) -> None:
        digest_date = expected_digest_date()
        now = datetime.now(ZoneInfo("Asia/Karachi"))
        if now.hour == 23 and now.minute < 1:
            return
        self._send(digest_date)

    def _send(self, digest_date) -> None:
        try:
            result = DashboardDigestService(container=self.container).send_for_date(digest_date)
            log.info("DairyOS nightly digest result: %s", result)
        except Exception:
            log.exception("DairyOS nightly digest failed for %s", digest_date)
