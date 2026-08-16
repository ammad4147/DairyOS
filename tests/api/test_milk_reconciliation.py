from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pytest

import dairyos.farm.production.services.milk_reconciliation_service as reconciliation_module
from dairyos.data.models.milk_disposition import MilkDisposition
from dairyos.farm.production.services.milk_reconciliation_service import (
    MilkReconciliationService,
)


@dataclass
class FakeTrendResult:
    payload: dict

    def summary(self):
        return dict(self.payload)


class FakeTrendService:
    def __init__(self, payload):
        self.payload = payload

    def generate(self, *, as_of_date, period_days):
        assert period_days == 7
        return FakeTrendResult(self.payload)


class FakeDispositionRepository:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.session = None

    def add(self, disposition):
        self.rows.append(disposition)
        return disposition

    save = add

    def get_by_date(self, production_date):
        return [
            row
            for row in self.rows
            if row.production_date == production_date
        ]

    def get_by_sale_id(self, sale_id):
        return next(
            (
                row
                for row in self.rows
                if row.sale_id == sale_id
            ),
            None,
        )


class FakeFindingRepository:
    def __init__(self):
        self.rows = []
        self.session = None

    def find_open_by_dedupe_key(self, dedupe_key):
        for row in self.rows:
            if (
                row.dedupe_key == dedupe_key
                and row.status != "RESOLVED"
            ):
                return row
        return None

    def count_opened_on(self, prefix):
        return sum(
            1
            for row in self.rows
            if row.finding_id.startswith(prefix)
        )

    def add(self, finding):
        self.rows.append(finding)
        return finding

    def get_by_finding_id(self, finding_id):
        return next(
            (
                row
                for row in self.rows
                if row.finding_id == finding_id
            ),
            None,
        )


class FakeFactory:
    def __init__(
        self,
        disposition_repository,
        finding_repository,
    ):
        self._disposition_repository = (
            disposition_repository
        )
        self._finding_repository = (
            finding_repository
        )

    def milk_dispositions(self):
        return self._disposition_repository

    def operational_findings(self):
        return self._finding_repository

    def close(self):
        return None


def _patch_trend(
    monkeypatch,
    *,
    complete: bool,
    daily_total: float | None,
):
    payload = {
        "complete": complete,
        "is_complete": complete,
        "daily_total": daily_total,
        "total_litres": daily_total,
        "total_yield": daily_total,
        "series": (
            [
                {
                    "date": "2026-08-15",
                    "total_yield": daily_total,
                }
            ]
            if complete and daily_total is not None
            else []
        ),
    }

    monkeypatch.setattr(
        reconciliation_module,
        "MilkProductionTrendIntelligenceService",
        lambda: FakeTrendService(payload),
    )


def _patch_factory(
    monkeypatch,
    disposition_repository,
    finding_repository,
):
    factory = FakeFactory(
        disposition_repository,
        finding_repository,
    )

    monkeypatch.setattr(
        reconciliation_module.RepositoryFactory,
        "create",
        staticmethod(lambda: factory),
    )

    return factory


def _service(repo):
    return MilkReconciliationService(
        disposition_repository=repo,
    )


def _sold(
    production_date,
    quantity,
    *,
    sale_id="SALE-001",
    price=225.0,
    amount_received=0.0,
):
    return MilkDisposition(
        production_date=production_date,
        disposition_type="SOLD",
        quantity_litres=quantity,
        sale_id=sale_id,
        counterparty="Buyer",
        selling_price_per_litre=price,
        amount_due=quantity * price,
        amount_received=amount_received,
        recorded_by="TEST",
    )


def _non_sale(
    production_date,
    disposition_type,
    quantity,
):
    return MilkDisposition(
        production_date=production_date,
        disposition_type=disposition_type,
        quantity_litres=quantity,
        amount_due=0.0,
        amount_received=0.0,
        recorded_by="TEST",
    )


def test_complete_fully_accounted_reconciles(
    monkeypatch,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository(
        [
            _sold(
                production_date,
                12.0,
            ),
            _non_sale(
                production_date,
                "CALF_FEED",
                8.0,
            ),
        ]
    )

    findings = FakeFindingRepository()

    _patch_trend(
        monkeypatch,
        complete=True,
        daily_total=20.0,
    )
    _patch_factory(
        monkeypatch,
        repo,
        findings,
    )

    result = _service(repo).reconcile(
        production_date,
        raise_finding=True,
    )

    assert result["production_complete"] is True
    assert result["produced_litres"] == 20.0
    assert result["accounted_litres"] == 20.0
    assert result["unaccounted_litres"] == 0.0
    assert result["over_accounted_litres"] == 0.0
    assert result["status"] == "RECONCILED"
    assert findings.rows == []


def test_complete_under_accounted_reports_unaccounted(
    monkeypatch,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository(
        [
            _sold(
                production_date,
                12.0,
            ),
        ]
    )

    findings = FakeFindingRepository()

    _patch_trend(
        monkeypatch,
        complete=True,
        daily_total=20.0,
    )
    _patch_factory(
        monkeypatch,
        repo,
        findings,
    )

    result = _service(repo).reconcile(
        production_date,
        raise_finding=True,
    )

    assert result["status"] == "UNACCOUNTED_PRODUCTION"
    assert result["produced_litres"] == 20.0
    assert result["accounted_litres"] == 12.0
    assert result["unaccounted_litres"] == 8.0
    assert result["over_accounted_litres"] == 0.0

    assert len(findings.rows) == 1
    assert findings.rows[0].severity == "HIGH"


def test_complete_over_accounted_reports_over_accounted(
    monkeypatch,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository(
        [
            _sold(
                production_date,
                25.0,
            ),
        ]
    )

    findings = FakeFindingRepository()

    _patch_trend(
        monkeypatch,
        complete=True,
        daily_total=20.0,
    )
    _patch_factory(
        monkeypatch,
        repo,
        findings,
    )

    result = _service(repo).reconcile(
        production_date,
        raise_finding=True,
    )

    assert result["status"] == "OVER_ACCOUNTED"
    assert result["produced_litres"] == 20.0
    assert result["accounted_litres"] == 25.0
    assert result["unaccounted_litres"] == 0.0
    assert result["over_accounted_litres"] == 5.0

    assert len(findings.rows) == 1
    assert findings.rows[0].severity == "CRITICAL"


def test_incomplete_production_reports_production_incomplete(
    monkeypatch,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository(
        [
            _sold(
                production_date,
                5.0,
            ),
        ]
    )

    findings = FakeFindingRepository()

    _patch_trend(
        monkeypatch,
        complete=False,
        daily_total=None,
    )
    _patch_factory(
        monkeypatch,
        repo,
        findings,
    )

    result = _service(repo).reconcile(
        production_date,
        raise_finding=True,
    )

    assert result["production_complete"] is False
    assert result["status"] == "PRODUCTION_INCOMPLETE"
    assert result["produced_litres"] is None
    assert result["accounted_litres"] == 5.0

    # Incomplete production must not raise a reconciliation exception.
    assert findings.rows == []


def test_missing_production_snapshot_reports_production_incomplete(
    monkeypatch,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository()
    findings = FakeFindingRepository()

    class EmptyTrend:
        def generate(self, *, as_of_date, period_days):
            return FakeTrendResult(
                {
                    "complete": False,
                    "is_complete": False,
                    "daily_total": None,
                    "total_litres": None,
                    "total_yield": None,
                    "series": [],
                }
            )

    monkeypatch.setattr(
        reconciliation_module,
        "MilkProductionTrendIntelligenceService",
        EmptyTrend,
    )

    _patch_factory(
        monkeypatch,
        repo,
        findings,
    )

    result = _service(repo).reconcile(
        production_date,
        raise_finding=True,
    )

    assert result["status"] == "PRODUCTION_INCOMPLETE"
    assert result["production_complete"] is False
    assert findings.rows == []


def test_sold_milk_creates_receivable():
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository()

    service = _service(repo)

    disposition = service.record_disposition(
        production_date=production_date,
        disposition_type="SOLD",
        quantity_litres=10.0,
        sale_id="SALE-001",
        counterparty="Buyer A",
        selling_price_per_litre=225.0,
        recorded_by="Operator",
    )

    assert disposition.disposition_type == "SOLD"
    assert disposition.quantity_litres == 10.0
    assert disposition.amount_due == 2250.0
    assert disposition.amount_received == 0.0
    assert disposition.receivable_outstanding == 2250.0


def test_duplicate_sale_id_is_rejected():
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository(
        [
            _sold(
                production_date,
                10.0,
                sale_id="SALE-001",
            )
        ]
    )

    service = _service(repo)

    with pytest.raises(
        ValueError,
        match="already recorded",
    ):
        service.record_disposition(
            production_date=production_date,
            disposition_type="SOLD",
            quantity_litres=4.0,
            sale_id="SALE-001",
            selling_price_per_litre=225.0,
        )


def test_sold_requires_sale_id():
    service = _service(
        FakeDispositionRepository()
    )

    with pytest.raises(
        ValueError,
        match="requires a sale_id",
    ):
        service.record_disposition(
            production_date=date(2026, 8, 15),
            disposition_type="SOLD",
            quantity_litres=4.0,
            selling_price_per_litre=225.0,
        )


def test_sold_requires_non_negative_price():
    service = _service(
        FakeDispositionRepository()
    )

    with pytest.raises(
        ValueError,
        match="non-negative",
    ):
        service.record_disposition(
            production_date=date(2026, 8, 15),
            disposition_type="SOLD",
            quantity_litres=4.0,
            sale_id="SALE-002",
            selling_price_per_litre=-1.0,
        )


@pytest.mark.parametrize(
    "disposition_type",
    [
        "CALF_FEED",
        "DOMESTIC_USE",
        "WASTAGE",
    ],
)
def test_non_sale_dispositions_are_accountable(
    disposition_type,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository()

    service = _service(repo)

    disposition = service.record_disposition(
        production_date=production_date,
        disposition_type=disposition_type,
        quantity_litres=3.5,
        sale_id="SHOULD-BE-DISCARDED",
        counterparty="Should be discarded",
        selling_price_per_litre=225.0,
    )

    assert disposition.disposition_type == disposition_type
    assert disposition.quantity_litres == 3.5
    assert disposition.sale_id is None
    assert disposition.counterparty is None
    assert disposition.selling_price_per_litre is None
    assert disposition.amount_due == 0.0


def test_reconciliation_finding_is_created(
    monkeypatch,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository(
        [
            _sold(
                production_date,
                10.0,
            )
        ]
    )

    findings = FakeFindingRepository()

    _patch_trend(
        monkeypatch,
        complete=True,
        daily_total=20.0,
    )

    _patch_factory(
        monkeypatch,
        repo,
        findings,
    )

    result = _service(repo).reconcile(
        production_date,
        raise_finding=True,
    )

    assert result["status"] == "UNACCOUNTED_PRODUCTION"
    assert len(findings.rows) == 1

    finding = findings.rows[0]

    assert finding.source_module == "MILK"
    assert finding.subject_type == "FARM"
    assert finding.subject_id == "MILK"
    assert (
        finding.dedupe_key
        == "MILK_RECONCILIATION:2026-08-15"
    )


def test_reconciliation_finding_is_deduplicated(
    monkeypatch,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository(
        [
            _sold(
                production_date,
                10.0,
            )
        ]
    )

    findings = FakeFindingRepository()

    _patch_trend(
        monkeypatch,
        complete=True,
        daily_total=20.0,
    )

    _patch_factory(
        monkeypatch,
        repo,
        findings,
    )

    first = _service(repo).reconcile(
        production_date,
        raise_finding=True,
    )

    second = _service(repo).reconcile(
        production_date,
        raise_finding=True,
    )

    assert first["status"] == "UNACCOUNTED_PRODUCTION"
    assert second["status"] == "UNACCOUNTED_PRODUCTION"

    assert len(findings.rows) == 1
    assert findings.rows[0].observation_count == 2


def test_reconciliation_is_date_isolated(
    monkeypatch,
):
    target_date = date(2026, 8, 15)
    other_date = date(2026, 8, 14)

    repo = FakeDispositionRepository(
        [
            _sold(
                target_date,
                20.0,
                sale_id="TARGET",
            ),
            _sold(
                other_date,
                99.0,
                sale_id="OTHER",
            ),
        ]
    )

    findings = FakeFindingRepository()

    _patch_trend(
        monkeypatch,
        complete=True,
        daily_total=20.0,
    )

    _patch_factory(
        monkeypatch,
        repo,
        findings,
    )

    result = _service(repo).reconcile(
        target_date,
        raise_finding=False,
    )

    assert result["production_date"] == (
        target_date.isoformat()
    )
    assert result["accounted_litres"] == 20.0
    assert result["status"] == "RECONCILED"


def test_incomplete_production_never_creates_finding(
    monkeypatch,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository(
        [
            _sold(
                production_date,
                100.0,
            )
        ]
    )

    findings = FakeFindingRepository()

    _patch_trend(
        monkeypatch,
        complete=False,
        daily_total=None,
    )

    _patch_factory(
        monkeypatch,
        repo,
        findings,
    )

    result = _service(repo).reconcile(
        production_date,
        raise_finding=True,
    )

    assert result["status"] == "PRODUCTION_INCOMPLETE"
    assert findings.rows == []
def test_complete_wastage_is_accounted_separately(
    monkeypatch,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository(
        [
            _sold(
                production_date,
                60.0,
            ),
            _non_sale(
                production_date,
                "WASTAGE",
                15.0,
            ),
            _non_sale(
                production_date,
                "DOMESTIC_USE",
                5.0,
            ),
        ]
    )
    findings = FakeFindingRepository()

    _patch_trend(
        monkeypatch,
        complete=True,
        daily_total=80.0,
    )
    _patch_factory(
        monkeypatch,
        repo,
        findings,
    )

    result = _service(repo).reconcile(
        production_date,
        raise_finding=True,
    )

    assert result["production_complete"] is True
    assert result["produced_litres"] == 80.0
    assert result["sold_litres"] == 60.0
    assert result["non_sale_accounted_litres"] == 20.0
    assert result["accounted_litres"] == 80.0
    assert result["unaccounted_litres"] == 0.0
    assert result["over_accounted_litres"] == 0.0
    assert result["status"] == "RECONCILED"
    assert findings.rows == []

def test_non_sale_milk_does_not_mask_unaccounted_production(
    monkeypatch,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository(
        [
            _sold(
                production_date,
                60.0,
            ),
            _non_sale(
                production_date,
                "WASTAGE",
                15.0,
            ),
        ]
    )
    findings = FakeFindingRepository()

    _patch_trend(
        monkeypatch,
        complete=True,
        daily_total=80.0,
    )
    _patch_factory(
        monkeypatch,
        repo,
        findings,
    )

    result = _service(repo).reconcile(
        production_date,
        raise_finding=True,
    )

    assert result["produced_litres"] == 80.0
    assert result["sold_litres"] == 60.0
    assert result["accounted_litres"] == 75.0
    assert result["unaccounted_litres"] == 5.0
    assert result["status"] == "UNACCOUNTED_PRODUCTION"
    assert len(findings.rows) == 1

def test_incomplete_day_with_non_sale_disposition_remains_incomplete(
    monkeypatch,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository(
        [
            _non_sale(
                production_date,
                "WASTAGE",
                15.0,
            ),
        ]
    )
    findings = FakeFindingRepository()

    _patch_trend(
        monkeypatch,
        complete=False,
        daily_total=None,
    )
    _patch_factory(
        monkeypatch,
        repo,
        findings,
    )

    result = _service(repo).reconcile(
        production_date,
        raise_finding=True,
    )

    assert result["production_complete"] is False
    assert result["produced_litres"] is None
    assert result["status"] == "PRODUCTION_INCOMPLETE"
    assert findings.rows == []

def test_withheld_disposition_is_rejected():
    production_date = date(2026, 8, 15)

    service = _service(
        FakeDispositionRepository()
    )

    with pytest.raises(
        ValueError,
        match="Unknown milk disposition",
    ):
        service.record_disposition(
            production_date=production_date,
            disposition_type="WITHHELD",
            quantity_litres=7.5,
            recorded_by="Operator",
        )

def test_disposition_quantity_must_not_over_allocate_known_production(
    monkeypatch,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository(
        [
            _sold(
                production_date,
                60.0,
            ),
            _non_sale(
                production_date,
                "WASTAGE",
                15.0,
            ),
        ]
    )

    _patch_trend(
        monkeypatch,
        complete=True,
        daily_total=80.0,
    )

    _patch_factory(
        monkeypatch,
        repo,
        FakeFindingRepository(),
    )

    service = _service(repo)

    with pytest.raises(
        ValueError,
        match="exceeds available production",
    ):
        service.record_disposition(
            production_date=production_date,
            disposition_type="WASTAGE",
            quantity_litres=6.0,
            recorded_by="Operator",
        )

def test_non_sale_disposition_retains_recorded_by_in_serialized_traceability(
    monkeypatch,
):
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository(
        [
            _non_sale(
                production_date,
                "WASTAGE",
                15.0,
            ),
        ]
    )

    service = _service(repo)

    item = service.record_disposition(
        production_date=production_date,
        disposition_type="WASTAGE",
        quantity_litres=5.0,
        notes="Damaged milk batch",
        recorded_by="Milking Operator",
    )

    payload = service._serialize_disposition(item)

    assert payload["disposition_type"] == "WASTAGE"
    assert payload["quantity_litres"] == 5.0
    assert payload["recorded_by"] == "Milking Operator"
    assert payload["notes"] == "Damaged milk batch"

def test_non_sale_disposition_cannot_carry_sale_metadata():
    service = _service(
        FakeDispositionRepository()
    )

    item = service.record_disposition(
        production_date=date(2026, 8, 15),
        disposition_type="WASTAGE",
        quantity_litres=5.0,
        sale_id="ILLEGAL-SALE",
        counterparty="Buyer",
        selling_price_per_litre=225.0,
        recorded_by="Operator",
    )

    assert item.sale_id is None
    assert item.counterparty is None
    assert item.selling_price_per_litre is None
    assert item.amount_due == 0.0

def test_duplicate_non_sale_dispositions_are_not_silently_collapsed():
    production_date = date(2026, 8, 15)

    repo = FakeDispositionRepository()

    service = _service(repo)

    first = service.record_disposition(
        production_date=production_date,
        disposition_type="WASTAGE",
        quantity_litres=5.0,
        recorded_by="Operator-1",
    )

    second = service.record_disposition(
        production_date=production_date,
        disposition_type="WASTAGE",
        quantity_litres=5.0,
        recorded_by="Operator-2",
    )

    assert first is not second
    assert len(repo.rows) == 2
    assert repo.rows[0] is first
    assert repo.rows[1] is second
    assert repo.rows[0].quantity_litres == 5.0
    assert repo.rows[1].quantity_litres == 5.0
    assert repo.rows[0].recorded_by == "Operator-1"
    assert repo.rows[1].recorded_by == "Operator-2"


