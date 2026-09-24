"""PostgreSQL-backed ownership for recurring application schedulers."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import text

from dairyos.platform.postgres_environment import isolated_postgres_environment

_SCHEDULER_LOCK_NAMESPACE = 746182935


def _lock_id(name: str) -> int:
    if not name or not name.isascii():
        raise ValueError("Scheduler lease names must be nonempty ASCII strings.")
    return (
        int.from_bytes(hashlib.sha256(name.encode("ascii")).digest()[:4], "big")
        & 0x7FFFFFFF
    )


@contextmanager
def scheduler_lease(name: str) -> Iterator[bool]:
    """Yield whether this process acquired the cross-process job lease.

    The PostgreSQL session-level advisory lock is held on a dedicated checked-out
    connection for the complete job action. Process termination closes the
    connection and releases ownership automatically.
    """
    from dairyos.data.database.session import engine

    lock_id = _lock_id(name)
    with isolated_postgres_environment(), engine.connect() as connection:
        acquired = bool(
            connection.execute(
                text("SELECT pg_try_advisory_lock(:namespace, :lock_id)"),
                {"namespace": _SCHEDULER_LOCK_NAMESPACE, "lock_id": lock_id},
            ).scalar_one()
        )
        try:
            yield acquired
        finally:
            if acquired:
                connection.execute(
                    text("SELECT pg_advisory_unlock(:namespace, :lock_id)"),
                    {"namespace": _SCHEDULER_LOCK_NAMESPACE, "lock_id": lock_id},
                )
                connection.commit()
