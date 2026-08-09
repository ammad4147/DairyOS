from dairyos.intelligence.integration.runtime_contract import (
    AutonomousRuntimeContract,
)


def test_runtime_contract_accepts_completed_runtime():

    contract = AutonomousRuntimeContract()

    result = {
        "runtime": {
            "status": "completed",
            "cycle_id": "test-cycle",
            "started_at": "2026-07-21T00:00:00+00:00",
            "completed_at": "2026-07-21T00:00:01+00:00",
            "stages": [
                "prediction",
                "decision",
            ],
            "stage_count": 2,
        }
    }

    assert contract.validate(
        result
    ) is True



def test_runtime_contract_rejects_missing_runtime():

    contract = AutonomousRuntimeContract()

    result = {}

    assert contract.validate(
        result
    ) is False



def test_runtime_contract_detects_missing_fields():

    contract = AutonomousRuntimeContract()

    result = {
        "runtime": {
            "status": "completed",
        }
    }

    missing = contract.missing_fields(
        result
    )

    assert "cycle_id" in missing
    assert "stages" in missing



def test_runtime_contract_rejects_stage_count_mismatch():

    contract = AutonomousRuntimeContract()

    result = {
        "runtime": {
            "status": "completed",
            "cycle_id": "test-cycle",
            "started_at": "start",
            "completed_at": "end",
            "stages": [
                "prediction",
            ],
            "stage_count": 5,
        }
    }

    assert contract.validate(
        result
    ) is False
