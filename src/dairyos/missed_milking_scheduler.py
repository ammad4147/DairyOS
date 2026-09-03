"""Daily missed-milking finding reconciliation owned by the backend runtime."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import datetime, time
from zoneinfo import ZoneInfo

from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.production.services.missed_milking_control_service import (
    MissedMilkingControlService,
)
from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService

log = logging.getLogger(__name__)

LAST_RECONCILED_DATE_KEY = "missed_milking_last_reconciled_date"
RUN_AFTER_LOCAL_TIME = time(0, 5)


class DailyMissedMilkingScheduler:
    """Reconcile completed milking dates once per farm-local day."""

    def __init__(
        self,
        *,
        interval_seconds: int = 30,
        run_after_local_time: time = RUN_AFTER_LOCAL_TIME,
        factory_provider: Callable = RepositoryFactory.create,
        now_provider: Callable[[ZoneInfo], datetime] | None = None,
    ):
        self.interval_seconds = max(5, int(interval_seconds))
        self.run_after_local_time = run_after_local_time
        self.factory_provider = factory_provider
        self.now_provider = now_provider or (lambda zone: datetime.now(zone))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop.clear()
        # Catch up once after startup if today's scheduled time has passed.
        self._run_if_due()
        self._thread = threading.Thread(
            target=self._loop,
            name="dairyos-missed-milking-scheduler",
            daemon=True,
        )
        self._thread.start()
        log.info(
            "Daily missed-milking scheduler started (farm-local run time=%s)",
            self.run_after_local_time.isoformat(timespec="minutes"),
        )

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None
        log.info("Daily missed-milking scheduler stopped")

    def _loop(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            self._run_if_due()

    def _run_if_due(self) -> bool:
        if not self._lock.acquire(blocking=False):
            return False

        factory = None
        try:
            factory = self.factory_provider()
            settings_repository = factory.app_settings()
            zone = FarmSettingsService(settings_repository).get_timezone_info()
            now = self.now_provider(zone).astimezone(zone)
            operational_date = now.date()
            slot = operational_date.isoformat()

            if now.time().replace(tzinfo=None) < self.run_after_local_time:
                return False
            if settings_repository.get(LAST_RECONCILED_DATE_KEY) == slot:
                return False

            result = MissedMilkingControlService(factory).reconcile(
                as_of_date=operational_date,
                lookback_days=31,
            )
            settings_repository.set(
                LAST_RECONCILED_DATE_KEY,
                slot,
                updated_by="MISSED_MILKING_SCHEDULER",
            )
            log.info(
                "Daily missed-milking reconciliation completed for farm date %s: %s",
                slot,
                result,
            )
            return True
        except Exception:
            if factory is not None:
                try:
                    factory.session.rollback()
                except Exception:
                    log.warning(
                        "Failed to roll back missed-milking scheduler session",
                        exc_info=True,
                    )
            log.exception("Daily missed-milking reconciliation failed")
            return False
        finally:
            if factory is not None:
                factory.close()
            self._lock.release()
