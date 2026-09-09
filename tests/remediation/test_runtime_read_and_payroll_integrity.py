from datetime import date
from pathlib import Path
from types import SimpleNamespace

from dairyos.post_calving_return_scheduler import PostCalvingReturnScheduler


ROOT = Path(__file__).resolve().parents[2]


class _Session:
    def __init__(self):
        self.rollback_count = 0
    def rollback(self):
        self.rollback_count += 1


class _Factory:
    def __init__(self):
        self.session = _Session()
        self.closed = False
    def close(self):
        self.closed = True


def test_tmr_get_is_read_only_for_post_calving_transitions():
    source = (ROOT / "src/dairyos/api/tmr.py").read_text(encoding="utf-8")
    get_block = source.split('@router.get("")', 1)[1].split(
        '@router.post("/stages")', 1
    )[0]
    assert "reconcile_due_post_calving_returns" not in get_block


def test_app_owns_post_calving_scheduler_lifecycle():
    source = (ROOT / "src/dairyos/app.py").read_text(encoding="utf-8")
    assert "post_calving_return_scheduler.start()" in source
    assert "post_calving_return_scheduler.stop()" in source


def test_scheduler_uses_fresh_factory_and_closes(monkeypatch):
    factory = _Factory()
    calls = []

    def reconcile(received, journal):
        calls.append((received, journal))
        return ["A-1"]

    monkeypatch.setattr(
        "dairyos.post_calving_return_scheduler.reconcile_due_post_calving_returns",
        reconcile,
    )
    scheduler = PostCalvingReturnScheduler(
        interval_seconds=60,
        factory_provider=lambda: factory,
    )
    assert scheduler._reconcile() == ["A-1"]
    assert calls == [(factory, None)]
    assert factory.closed


def test_scheduler_rolls_back_and_does_not_raise_on_failure(monkeypatch):
    factory = _Factory()

    def fail(*_args):
        raise RuntimeError("injected")

    monkeypatch.setattr(
        "dairyos.post_calving_return_scheduler.reconcile_due_post_calving_returns",
        fail,
    )
    scheduler = PostCalvingReturnScheduler(
        interval_seconds=60,
        factory_provider=lambda: factory,
    )
    assert scheduler._reconcile() == []
    assert factory.session.rollback_count == 1
    assert factory.closed


def test_payroll_source_rejects_negative_draft_and_uses_operational_date():
    source = (ROOT / "src/dairyos/api/payroll.py").read_text(encoding="utf-8")
    create_block = source.split("def create_payroll", 1)[1].split(
        '@router.post("/{record_id}/pay")', 1
    )[0]
    assert "if record.net_pay < 0:" in create_block
    pay_block = source.split("def _pay_payroll", 1)[1]
    assert "OperationalDateAuthority" in pay_block
    assert "utcnow().date()" not in pay_block


def test_health_fk_indexes_have_migration_parity():
    migration = (
        ROOT
        / "db_migrations/versions/20260910_02_forensic_index_parity.py"
    ).read_text(encoding="utf-8")
    assert "ix_health_observation_health_case_id" in migration
    assert "ix_treatment_record_health_case_id" in migration
