"""Farm-local daily pre-summary whole-herd TMR cost lock."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import time

from dairyos.data.repositories.repository_factory import (
    RepositoryFactory,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)
from dairyos.platform.scheduler.leases import scheduler_lease

log = logging.getLogger(__name__)

# Lock the current operational day's TMR cost at the approved mid-day
# farm-local operational point.
# Historical days are deliberately never reconstructed from the current Animal
# Register: without an immutable same-day population authority, backdating a
# snapshot would fabricate historical herd strength and Feed Cost/L.
RUN_AFTER_LOCAL_TIME = time(12, 0)


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
            self.run_after_local_time.isoformat(timespec="minutes"),
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
            with scheduler_lease("tmr_daily_cost") as acquired:
                if not acquired:
                    return False
                factory = self.factory_provider()
                authority = OperationalDateAuthority(repository_factory=factory)
                now = authority.current_datetime()

                # A missed prior-day lock cannot be reconstructed safely from the
                # current Animal Register. Before today's lock window, fail closed
                # and let historical TMR authority remain explicitly missing.
                if now.time().replace(tzinfo=None) < self.run_after_local_time:
                    return False

                from dairyos.api.tmr import lock_daily_tmr_cost_snapshot

                operational_date = authority.current_date()
                result = lock_daily_tmr_cost_snapshot(
                    factory,
                    operational_date=operational_date,
                )

                if result.get("created"):
                    log.info(
                        "Daily TMR cost locked for farm date %s: %.4f",
                        result["operational_date"],
                        float(result["total_herd_feed_cost_per_day"]),
                    )

                return bool(result.get("created"))

        except Exception:
            if factory is not None:
                try:
                    factory.session.rollback()
                except Exception:
                    log.warning(
                        "Failed to roll back daily TMR scheduler session",
                        exc_info=True,
                    )

            log.exception("Daily TMR cost lock failed")
            return False

        finally:
            if factory is not None:
                factory.close()
            self._lock.release()
