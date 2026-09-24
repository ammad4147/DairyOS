"""Cross-process scheduler ownership uses PostgreSQL advisory locks."""

from __future__ import annotations

from uuid import uuid4

from dairyos.platform.scheduler.leases import scheduler_lease


def test_scheduler_lease_excludes_a_second_database_connection():
    lease_name = f"test_{uuid4().hex}"

    with scheduler_lease(lease_name) as first:
        assert first is True
        with scheduler_lease(lease_name) as concurrent:
            assert concurrent is False

    with scheduler_lease(lease_name) as after_release:
        assert after_release is True


def test_different_schedulers_have_independent_leases():
    suffix = uuid4().hex

    with (
        scheduler_lease(f"feed_{suffix}") as feed,
        scheduler_lease(f"email_{suffix}") as email,
    ):
        assert feed is True
        assert email is True
