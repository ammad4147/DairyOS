"""Farm-local daily pre-summary whole-herd TMR cost lock."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import timedelta, time

from dairyos.data.repositories.repository_factory import (
    RepositoryFactory,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)

log = logging.getLogger(__name__)

# The nightly operational summary is finalized at 23:00 farm-local time.
# Lock the completed day's TMR cost shortly before that report slot so the
# summary consumes a stable, end-of-day authority.
RUN_AFTER_LOCAL_TIME = time(22, 55)


class DailyTMRCostScheduler:
    """Lock one immutable whole-herd TMR cost per farm operational day."""

    def __init__(
        self,
        *,
        interval_seconds: int = 30,
        run_after_local_time: time = RUN_AFTER_LOCAL_TIME,
        factory_provider: Callable = RepositoryFactory.create,
    ):
        self.interval_seconds = max(5, int(interval_seconds))
        self.run_after_local_time = run_after_local_time
        self.factory_provider = factory_provider
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop.clear()

        # Catch up if DairyOS starts after the previous farm-local summary slot.
        self._run_if_due()

        self._thread = threading.Thread(
            target=self._loop,
            name="dairyos-tmr-daily-cost-scheduler",
            daemon=True,
        )
        self._thread.start()

        log.info(
            "Daily TMR cost scheduler started "
            "(farm-local lock time=%s)",
            self.run_after_local_time.isoformat(
                timespec="minutes"
            ),
        )

    def stop(self) -> None:
        self._stop.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

        self._thread = None

        log.info("Daily TMR cost scheduler stopped")

    def _loop(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            self._run_if_due()

    def _run_if_due(self) -> bool:
        if not self._lock.acquire(blocking=False):
            return False

        factory = None

        try:
            factory = self.factory_provider()

            authority = OperationalDateAuthority(
                repository_factory=factory,
            )

            now = authority.current_datetime()

            from dairyos.api.tmr import (
                lock_daily_tmr_cost_snapshot,
            )

            operational_date = authority.current_date()
            # Before tonight's 22:55 lock window, a startup belongs to the
            # catch-up path for yesterday. Once the window opens, finalize
            # today's completed operational record for the 23:00 summary.
            if now.time().replace(tzinfo=None) < self.run_after_local_time:
                operational_date -= timedelta(days=1)

            result = lock_daily_tmr_cost_snapshot(
                factory,
                operational_date=operational_date,
            )

            if result.get("created"):
                log.info(
                    "Daily TMR cost locked for farm date %s: %.4f",
                    result["operational_date"],
                    float(
                        result[
                            "total_herd_feed_cost_per_day"
                        ]
                    ),
                )

            return bool(result.get("created"))

        except Exception:
            if factory is not None:
                try:
                    factory.session.rollback()
                except Exception:
                    pass

            log.exception(
                "Daily TMR cost lock failed"
            )
            return False

        finally:
            if factory is not None:
                factory.close()

            self._lock.release()
