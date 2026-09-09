from __future__ import annotations

import threading
import time

from dairyos.post_calving_return_scheduler import PostCalvingReturnScheduler


class _Factory:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

    class _Session:
        def rollback(self):
            pass

    session = _Session()


def test_scheduler_start_never_waits_for_immediate_reconciliation(monkeypatch):
    entered = threading.Event()
    release = threading.Event()
    factory = _Factory()

    def blocking_reconcile(_factory, _journal):
        entered.set()
        release.wait(timeout=2)
        return []

    monkeypatch.setattr(
        "dairyos.post_calving_return_scheduler.reconcile_due_post_calving_returns",
        blocking_reconcile,
    )

    scheduler = PostCalvingReturnScheduler(
        interval_seconds=60,
        factory_provider=lambda: factory,
    )

    started_at = time.monotonic()
    scheduler.start()
    elapsed = time.monotonic() - started_at

    assert elapsed < 0.5, f"scheduler.start() blocked for {elapsed:.3f}s"
    assert entered.wait(timeout=1), "background reconciliation did not start"
    assert scheduler._thread is not None
    assert scheduler._thread.is_alive()

    release.set()
    scheduler.stop()

    assert factory.closed is True


def test_post_calving_row_lock_is_fail_fast_nowait():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    source = (
        root
        / "src"
        / "dairyos"
        / "farm"
        / "reproduction"
        / "services"
        / "post_calving_return_service.py"
    ).read_text(encoding="utf-8")

    assert ".with_for_update(nowait=True)" in source
