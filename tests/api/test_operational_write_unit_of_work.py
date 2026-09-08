"""Failure injection against disposable PostgreSQL, never a farm database."""

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from sqlalchemy import event, select
from sqlalchemy.orm import Session

from dairyos.app import container
from dairyos.application.operational_write import OperationalWriteService, RequestIdentityConflict
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.operational_write import OperationalWrite, OperationalProjectionOutbox
from dairyos.farm.inputs.repository.operational_input_repository import OperationalInputRepository
from dairyos.farm.inputs.services.input_ingestion_service import InputIngestionService


@pytest.fixture
def service(client, tmp_path):
    ingestion = InputIngestionService(
        registry=SimpleNamespace(validate=lambda *args: None),
        repository=OperationalInputRepository(tmp_path / "inputs.json"),
    )
    return OperationalWriteService(container.repository_factory.session.get_bind(), ingestion)


def write(factory, gateway):
    record = FinancialTransaction(transaction_type="EXPENSE", category="OTHER_OPERATING", amount=12)
    factory.financial().add(record)  # Legacy repository calls commit internally.
    gateway.record("financial", {"amount": 12}, "tester")
    return {"id": record.id, "amount": 12}


def counts(service):
    with Session(service.engine) as session:
        return tuple(session.query(model).count() for model in (
            FinancialTransaction, EventJournalModel, OperationalProjectionOutbox, OperationalWrite
        ))


def test_domain_journal_and_intent_invisible_until_single_commit(service):
    def mutation(factory, gateway):
        result = write(factory, gateway)
        assert counts(service) == (0, 0, 0, 0)
        assert service.ingestion.repository.list_all() == []
        return result

    response = service.execute(request_id="atomic", request={"amount": 12}, mutation=mutation)
    assert counts(service) == (1, 1, 1, 1)
    assert response["projection_status"] == "DELIVERED"


@pytest.mark.parametrize("failure", ["domain", "journal", "outbox", "response"])
def test_failure_rolls_back_every_authoritative_component(service, failure):
    model = EventJournalModel if failure == "journal" else OperationalProjectionOutbox

    def reject(*args):
        raise RuntimeError("injected persistence failure")

    def mutation(factory, gateway):
        if failure == "domain":
            factory.financial().add(FinancialTransaction(transaction_type="EXPENSE", category="OTHER_OPERATING", amount=12))
            raise RuntimeError("injected persistence failure")
        result = write(factory, gateway)
        return {"amount": float("nan")} if failure == "response" else result

    if failure in {"journal", "outbox"}:
        event.listen(model, "before_insert", reject)
    try:
        with pytest.raises((RuntimeError, ValueError)):
            service.execute(request_id="rollback", request={}, mutation=mutation)
    finally:
        if failure in {"journal", "outbox"}:
            event.remove(model, "before_insert", reject)
    assert counts(service) == (0, 0, 0, 0)
    assert service.ingestion.repository.list_all() == []


@pytest.mark.parametrize("failure", [PermissionError("denied"), TypeError("serialization")])
def test_projection_failure_is_accepted_and_survives_new_service(service, monkeypatch, failure):
    repository = service.ingestion.repository

    def reject():
        raise failure

    with monkeypatch.context() as patch:
        patch.setattr(repository, "_persist", reject)
        result = service.execute(request_id="restart", request={}, mutation=write)
    assert result["persistence_status"] == "ACCEPTED"
    assert result["projection_status"] == "DEGRADED"
    assert counts(service) == (1, 1, 1, 1)
    assert repository.list_all() == []
    restarted = OperationalWriteService(service.engine, InputIngestionService(
        registry=service.ingestion.registry,
        repository=OperationalInputRepository(repository.storage_path),
    ))
    assert restarted.deliver_pending()["projection_status"] == "DELIVERED"
    assert len(restarted.ingestion.repository.list_all()) == 1
    assert restarted.deliver_pending()["projection_status"] == "DELIVERED"
    assert counts(service) == (1, 1, 1, 1)


def test_duplicate_submission_and_conflicting_identity(service):
    first = service.execute(request_id="retry", request={"amount": 12}, mutation=write)
    second = service.execute(request_id="retry", request={"amount": 12}, mutation=write)
    assert first["id"] == second["id"]
    with pytest.raises(RequestIdentityConflict):
        service.execute(request_id="retry", request={"amount": 99}, mutation=write)
    assert counts(service) == (1, 1, 1, 1)
    assert len(service.ingestion.repository.list_all()) == 1


def test_concurrent_retry_does_not_repeat_domain_write(service):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: service.execute(request_id="concurrent", request={}, mutation=write), range(2)))
    assert results[0]["id"] == results[1]["id"]
    assert counts(service) == (1, 1, 1, 1)
    assert len(service.ingestion.repository.list_all()) == 1


def test_secondary_failure_after_json_write_retries_same_event(service, monkeypatch):
    delivered = []

    def reject(event):
        delivered.append(event.event_id)
        raise RuntimeError("secondary failure")

    service.ingestion.event_publisher = reject
    result = service.execute(request_id="secondary", request={}, mutation=write)
    assert result["projection_status"] == "DEGRADED"
    service.ingestion.event_publisher = lambda event: delivered.append(event.event_id)
    assert service.deliver_pending()["projection_status"] == "DELIVERED"
    assert len(set(delivered)) == 1
    assert len(service.ingestion.repository.list_all()) == 1
    with Session(service.engine) as session:
        row = session.scalar(select(OperationalProjectionOutbox))
        assert row.attempts == 2
        assert row.last_error is None
