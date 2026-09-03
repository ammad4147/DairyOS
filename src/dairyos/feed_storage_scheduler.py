from __future__ import annotations

import logging
import threading

from dairyos.data.repositories.repository_factory import (
    RepositoryFactory,
)


log = logging.getLogger(__name__)


class FeedStorageScheduler:
    """
    Runtime-owned automatic TMR Feed Storage reconciliation.

    This scheduler is operational authority, not a UI convenience:
    - it reconciles immediately when DairyOS starts;
    - it reconciles periodically while DairyOS is running;
    - it follows OperationalDateAuthority through the governed
      reconciliation service;
    - GET requests remain read-only;
    - current-day reconciliation stays idempotent;
    - closed materialised days remain immutable.
    """

    def __init__(
        self,
        *,
        interval_seconds: int = 60,
    ):
        self.interval_seconds = max(
            10,
            int(interval_seconds),
        )
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if (
            self._thread
            and self._thread.is_alive()
        ):
            return

        self._stop.clear()

        # Do not wait for a browser request or the first timer tick.
        self._reconcile()

        self._thread = threading.Thread(
            target=self._loop,
            name="dairyos-feed-storage-scheduler",
            daemon=True,
        )
        self._thread.start()

        log.info(
            "Feed Storage scheduler started "
            "(interval=%ss)",
            self.interval_seconds,
        )

    def stop(self) -> None:
        self._stop.set()

        if (
            self._thread
            and self._thread.is_alive()
        ):
            self._thread.join(timeout=2)

        self._thread = None

        log.info(
            "Feed Storage scheduler stopped"
        )

    def _loop(self) -> None:
        while not self._stop.wait(
            self.interval_seconds
        ):
            self._reconcile()

    def _reconcile(self) -> None:
        # Lazy import avoids application-bootstrap import cycles.
        from dairyos.api.feed_inventory import (
            reconcile_tmr_feed_storage,
        )

        factory = RepositoryFactory.create()

        try:
            result = reconcile_tmr_feed_storage(
                factory
            )

            log.info(
                "Feed Storage automatic TMR "
                "reconciliation result: %s",
                result,
            )
        except Exception:
            try:
                factory.session.rollback()
            except Exception:
                pass

            log.exception(
                "Feed Storage automatic TMR "
                "reconciliation failed"
            )
        finally:
            factory.close()
