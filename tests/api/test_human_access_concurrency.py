from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from fastapi.testclient import TestClient

from dairyos.api.human_access import _hash_pin
from dairyos.data.models.human_identity import HumanIdentity, HumanSession
from dairyos.data.repositories.repository_factory import RepositoryFactory


def _clear_human_access_rows() -> None:
    factory = RepositoryFactory.create()
    try:
        factory.session.query(HumanSession).delete(synchronize_session=False)
        factory.session.query(HumanIdentity).delete(synchronize_session=False)
        factory.session.commit()
    finally:
        factory.close()


def test_concurrent_first_use_creates_exactly_one_primary_admin(
    client: TestClient,
):
    _clear_human_access_rows()
    request_count = 6
    start = Barrier(request_count)

    def submit(index: int):
        start.wait(timeout=10)
        return client.post(
            "/human-access/bootstrap",
            json={
                "display_name": f"Bootstrap Test {index}",
                "pin": "4826",
                "pin_confirmation": "4826",
            },
        )

    try:
        with ThreadPoolExecutor(max_workers=request_count) as pool:
            responses = list(pool.map(submit, range(request_count)))

        statuses = sorted(response.status_code for response in responses)
        assert statuses == [200] + [409] * (request_count - 1)

        factory = RepositoryFactory.create()
        try:
            primary_admins = factory.session.query(HumanIdentity).filter_by(
                role="PRIMARY_ADMIN", active=True
            ).all()
            assert len(primary_admins) == 1
        finally:
            factory.close()
    finally:
        _clear_human_access_rows()


def test_concurrent_invalid_pins_preserve_identity_lockout_threshold(
    client: TestClient,
):
    _clear_human_access_rows()
    pin_hash, pin_salt = _hash_pin("4826")
    factory = RepositoryFactory.create()
    try:
        identity = HumanIdentity(
            display_name="Lockout Test Operator",
            entry_group="MILK_OPERATOR",
            role="MILKER",
            pin_hash=pin_hash,
            pin_salt=pin_salt,
        )
        factory.session.add(identity)
        factory.session.commit()
        identity_id = identity.id
    finally:
        factory.close()

    request_count = 8
    start = Barrier(request_count)

    def submit(_index: int):
        start.wait(timeout=10)
        return client.post(
            "/human-access/login",
            json={"identity_id": identity_id, "pin": "0000"},
        )

    try:
        with ThreadPoolExecutor(max_workers=request_count) as pool:
            responses = list(pool.map(submit, range(request_count)))

        statuses = sorted(response.status_code for response in responses)
        assert statuses == [401] * 5 + [423] * (request_count - 5)

        factory = RepositoryFactory.create()
        try:
            identity = factory.session.get(HumanIdentity, identity_id)
            assert identity is not None
            assert identity.failed_pin_attempts == 0
            assert identity.locked_until is not None
        finally:
            factory.close()
    finally:
        _clear_human_access_rows()
