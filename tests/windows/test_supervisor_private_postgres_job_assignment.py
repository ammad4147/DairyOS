from __future__ import annotations

import pytest

from dairyos.windows import supervisor


class _Job:
    def __init__(self, error: BaseException | None = None) -> None:
        self.error = error
        self.assigned = []

    def assign_pid(self, pid: int) -> None:
        self.assigned.append(pid)
        if self.error is not None:
            raise self.error


def _permission_error(winerror: int) -> PermissionError:
    error = PermissionError(winerror, "synthetic job assignment failure")
    error.winerror = winerror
    return error


def test_private_postgres_job_assignment_success_is_reported():
    job = _Job()

    assert supervisor.assign_private_postgres_to_job(job, 12345) is True
    assert job.assigned == [12345]


def test_access_denied_job_assignment_does_not_block_desktop_startup():
    job = _Job(_permission_error(5))

    assert supervisor.assign_private_postgres_to_job(job, 12345) is False
    assert job.assigned == [12345]


def test_other_job_assignment_permission_failures_remain_fail_closed():
    job = _Job(_permission_error(1314))

    with pytest.raises(PermissionError) as exc_info:
        supervisor.assign_private_postgres_to_job(job, 12345)

    assert getattr(exc_info.value, "winerror", None) == 1314
