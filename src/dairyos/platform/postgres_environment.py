"""Scoped isolation for libpq's process-wide environment inputs."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import os
import threading


POSTGRES_ENVIRONMENT_VARIABLES = frozenset(
    {
        "PGAPPNAME",
        "PGCHANNELBINDING",
        "PGCLIENTENCODING",
        "PGCONNECT_TIMEOUT",
        "PGDATABASE",
        "PGDATA",
        "PGGSSENCMODE",
        "PGGSSLIB",
        "PGHOST",
        "PGHOSTADDR",
        "PGKRBSRVNAME",
        "PGOPTIONS",
        "PGPASSFILE",
        "PGPASSWORD",
        "PGPORT",
        "PGREQUIREPEER",
        "PGREQUIRESSL",
        "PGSERVICE",
        "PGSERVICEFILE",
        "PGSYSCONFDIR",
        "PGSSLCERT",
        "PGSSLCRL",
        "PGSSLCRLDIR",
        "PGSSLKEY",
        "PGSSLMODE",
        "PGSSLROOTCERT",
        "PGSSLSNI",
        "PGTARGETSESSIONATTRS",
        "PGUSER",
    }
)

_POSTGRES_ENVIRONMENT_LOCK = threading.RLock()


@contextmanager
def isolated_postgres_environment() -> Iterator[None]:
    """Temporarily remove ambient libpq authority and restore it exactly."""
    with _POSTGRES_ENVIRONMENT_LOCK:
        previous = {
            name: (name in os.environ, os.environ.get(name))
            for name in POSTGRES_ENVIRONMENT_VARIABLES
        }
        try:
            for name in POSTGRES_ENVIRONMENT_VARIABLES:
                os.environ.pop(name, None)
            yield
        finally:
            for name, (existed, value) in previous.items():
                if existed:
                    os.environ[name] = "" if value is None else value
                else:
                    os.environ.pop(name, None)
