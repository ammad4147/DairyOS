"""Shared UTC "now" helper (2026-08-14).

`datetime.utcnow()` is deprecated (Python 3.12+) in favour of
`datetime.now(datetime.UTC)`, which returns a timezone-AWARE datetime.
Every DateTime column and dataclass timestamp field across DairyOS today
is naive (no tzinfo) -- the Postgres columns are `TIMESTAMP WITHOUT TIME
ZONE`, and comparisons throughout the codebase (e.g.
`observed_at >= cutoff`, `withdrawal_until > now`) mix naive values on both
sides. Swapping in an aware datetime everywhere would risk
aware-vs-naive `TypeError`s and silent serialization/comparison drift
across dozens of call sites -- a real migration, not a warning cleanup,
and out of scope here.

`utcnow()` is the drop-in replacement used throughout this codebase
instead: it produces the exact same *value* `datetime.utcnow()` did (naive,
UTC clock), just without the deprecated call, by computing an aware UTC
instant and stripping the tzinfo back off before returning it. This keeps
every existing comparison, persisted column, and serialized timestamp
working unchanged.

If DairyOS later adopts timezone-aware timestamps end-to-end (Python
representation, SQLAlchemy columns, Postgres columns, and every comparison
audited together), this helper is the one place that change happens --
not scattered across every call site again.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC datetime -- see module docstring for why naive."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
