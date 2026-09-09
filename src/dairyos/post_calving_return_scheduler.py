"""Runtime authority for planned post-calving returns to milking."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.reproduction.services.post_calving_return_service import (
    reconcile_due_post_calving_returns,
)

log = logging.getLogger(__name__)


class PostCalvingReturnScheduler:
    """Persist due planned returns independently of operator read screens."""

    def __init__(
        self,
        *,
        interval_seconds: int = 60,
        factory_provider: Callable = RepositoryFactory.create,
    ):
        self.interval_seconds = max(5, int(interval_seconds))
        self.factory_provider = factory_provider
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._reconcile()
        self._thread = threading.Thread(
            target=self._loop,
            name="dairyos-post-calving-return-scheduler",
            daemon=True,
        )
        self._thread.start()
        log.info("Post-calving return scheduler started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None
        log.info("Post-calving return scheduler stopped")

    def _loop(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            self._reconcile()

    def _reconcile(self) -> list[str]:
        if not self._lock.acquire(blocking=False):
            return []

        factory = None
        try:
            factory = self.factory_provider()
            applied = reconcile_due_post_calving_returns(
                factory,
                None,
            )
            if applied:
                log.info(
                    "Applied planned post-calving returns: %s",
                    ", ".join(applied),
                )
            return applied
        except Exception:
            if factory is not None:
                try:
                    factory.session.rollback()
                except Exception:
                    log.warning(
                        "Failed to roll back post-calving scheduler session",
                        exc_info=True,
                    )
            log.exception("Post-calving return reconciliation failed")
            return []
        finally:
            if factory is not None:
                factory.close()
            self._lock.release()
