from __future__ import annotations

import logging
import threading
from datetime import datetime, time
from zoneinfo import ZoneInfo

from dairyos.core.time_utils import utcnow
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.settings.services.deployment_control_service import DeploymentControlService
from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService
from .digest import DashboardDigestService, expected_digest_date

log = logging.getLogger(__name__)
_LAST_STARTUP_KEY = "email_scheduler_last_startup_utc"


class NightlyEmailScheduler:
    """Lifecycle-owned scheduler using farm timezone and deployment activation."""

    def __init__(self, *, container, interval_seconds: int = 30):
        self.container = container
        self.interval_seconds = max(5, int(interval_seconds))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_attempted_slot: str | None = None

    def _settings(self) -> tuple[ZoneInfo, bool]:
        factory = RepositoryFactory.create()
        try:
            settings = FarmSettingsService(factory.app_settings())
            return settings.get_timezone_info(), DeploymentControlService(settings).is_deployed()
        finally:
            factory.close()

    def _zone(self) -> ZoneInfo:
        zone, _ = self._settings()
        return zone

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop.clear()
        self._last_attempted_slot = None
        current = utcnow()
        previous = None
        _zone, deployed = self._settings()

        # Configuration alone must not generate catch-up work. Once deployed,
        # only later scheduler starts may legitimately perform a catch-up.
        if deployed:
            previous = self._previous_startup()
            self._record_startup(current)
            self._run_catch_up(previous, current)
        else:
            log.info("Nightly email scheduler waiting for explicit deployment activation")

        self._thread = threading.Thread(
            target=self._loop,
            name="dairyos-email-scheduler",
            daemon=True,
        )
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
            factory.app_settings().set(
                _LAST_STARTUP_KEY,
                when.isoformat(),
                updated_by="EMAIL_SCHEDULER",
            )
        finally:
            factory.close()

    def _loop(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            zone, deployed = self._settings()
            if not deployed:
                continue
            now = datetime.now(zone)
            if now.hour == 23 and now.minute == 0:
                slot = now.date().isoformat()
                if slot != self._last_attempted_slot:
                    self._last_attempted_slot = slot
                    self._send(now.date())

    def _run_catch_up(self, previous: datetime | None, current: datetime) -> None:
        zone = self._zone()
        current_local = current.astimezone(zone)
        digest_date = expected_digest_date(current_local)
        expected_slot = datetime.combine(digest_date, time(23, 0), tzinfo=zone)

        if current_local < expected_slot:
            return

        if previous is None:
            self._send(digest_date)
            return

        previous_local = previous.astimezone(zone)
        if previous_local < expected_slot:
            self._send(digest_date)

    def _send(self, digest_date) -> None:
        try:
            result = DashboardDigestService(container=self.container).send_for_date(digest_date)
            log.info("DairyOS nightly digest result: %s", result)
        except Exception:
            log.exception("DairyOS nightly digest failed for %s", digest_date)
