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


def test_supervisor_logging_is_durable_but_not_startup_critical(monkeypatch, tmp_path):
    monkeypatch.setenv("DAIRYOS_DATA_DIR", str(tmp_path))
    path = supervisor.configure_supervisor_logging("INFO")

    assert path == tmp_path / "logs" / "supervisor.log"
    supervisor.LOG.info("synthetic installed-runtime diagnostic")
    for handler in supervisor.logging.getLogger().handlers:
        flush = getattr(handler, "flush", None)
        if flush is not None:
            flush()
    assert "synthetic installed-runtime diagnostic" in path.read_text(encoding="utf-8")


def test_job_fallback_rationale_identifies_openprocess_security_context():
    import inspect

    source = inspect.getsource(supervisor.assign_private_postgres_to_job)
    assert "security context" in source
    assert "OpenProcess" in source
    assert "job hierarchy prevents" not in source
