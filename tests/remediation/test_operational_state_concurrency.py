from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier
from time import sleep
from uuid import uuid4

import pytest

from dairyos.data.database.models.operational_state_model import (
    OperationalStateModel,
)
from dairyos.data.repositories.operational_state_mutation import (
    mutate_operational_state,
)
from dairyos.data.repositories.repository_factory import RepositoryFactory


def _concurrent_mutation(farm_id, barrier, mutation):
    factory = RepositoryFactory.create()
    try:
        barrier.wait(timeout=5)
        mutate_operational_state(
            factory.session,
            farm_id=farm_id,
            operational_date=date(2026, 9, 19),
            mutation=mutation,
        )
        factory.session.commit()
    except Exception:
        factory.session.rollback()
        raise
    finally:
        factory.close()


def _load_state(farm_id):
    factory = RepositoryFactory.create()
    try:
        rows = (
            factory.session.query(OperationalStateModel)
            .filter(OperationalStateModel.farm_id == farm_id)
            .all()
        )
        assert len(rows) == 1
        return dict(rows[0].state_payload or {})
    finally:
        factory.close()


def test_concurrent_first_row_different_namespaces_preserve_both(client):
    del client
    farm_id = f"OSTATE-DIFFERENT-{uuid4().hex}"
    barrier = Barrier(2)

    def set_ration(payload):
        sleep(0.1)
        payload["ration_plans"] = [{"plan_id": "RATION-1"}]
        return payload

    def set_welfare(payload):
        sleep(0.1)
        payload["animal_welfare_observations"] = [{"score": 92}]
        return payload

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(_concurrent_mutation, farm_id, barrier, set_ration),
            pool.submit(_concurrent_mutation, farm_id, barrier, set_welfare),
        ]
        for future in futures:
            future.result(timeout=10)

    payload = _load_state(farm_id)
    assert payload["ration_plans"] == [{"plan_id": "RATION-1"}]
    assert payload["animal_welfare_observations"] == [{"score": 92}]


def test_concurrent_same_namespace_appends_preserve_every_observation(client):
    del client
    farm_id = f"OSTATE-SAME-{uuid4().hex}"
    barrier = Barrier(2)

    def append_observation(observation_id):
        def mutation(payload):
            history = list(payload.get("heat_stress_observations", []))
            sleep(0.1)
            history.append({"observation_id": observation_id})
            payload["heat_stress_observations"] = history
            return payload

        return mutation

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(
                _concurrent_mutation,
                farm_id,
                barrier,
                append_observation("OBS-1"),
            ),
            pool.submit(
                _concurrent_mutation,
                farm_id,
                barrier,
                append_observation("OBS-2"),
            ),
        ]
        for future in futures:
            future.result(timeout=10)

    payload = _load_state(farm_id)
    assert {
        item["observation_id"]
        for item in payload["heat_stress_observations"]
    } == {"OBS-1", "OBS-2"}


def test_rollback_releases_lock_and_leaves_no_partial_state(client):
    del client
    farm_id = f"OSTATE-ROLLBACK-{uuid4().hex}"
    failed = RepositoryFactory.create()
    try:
        def fail_after_change(payload):
            payload["transient"] = True
            raise RuntimeError("injected operational-state failure")

        with pytest.raises(
            RuntimeError,
            match="injected operational-state failure",
        ):
            mutate_operational_state(
                failed.session,
                farm_id=farm_id,
                operational_date=date(2026, 9, 19),
                mutation=fail_after_change,
            )
        failed.session.rollback()
    finally:
        failed.close()

    committed = RepositoryFactory.create()
    try:
        mutate_operational_state(
            committed.session,
            farm_id=farm_id,
            operational_date=date(2026, 9, 19),
            mutation=lambda payload: {**payload, "durable": True},
        )
        committed.session.commit()
    finally:
        committed.close()

    assert _load_state(farm_id) == {"durable": True}
