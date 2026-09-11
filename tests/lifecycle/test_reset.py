import json

from dairyos.lifecycle.reset import (
    FILE_PROJECTION_FILENAMES,
    clear_file_projections,
    verify_file_projection_zero_state,
)


def test_reset_clears_event_owned_file_projections(tmp_path):
    storage = tmp_path / "storage"
    storage.mkdir()
    for filename in FILE_PROJECTION_FILENAMES:
        (storage / filename).write_text(
            json.dumps([{"pre_reset": True}]),
            encoding="utf-8",
        )

    cleared = clear_file_projections(tmp_path)

    assert len(cleared) == len(FILE_PROJECTION_FILENAMES)
    assert verify_file_projection_zero_state(tmp_path) == {}
    for filename in FILE_PROJECTION_FILENAMES:
        assert json.loads((storage / filename).read_text(encoding="utf-8")) == []


def test_reset_zero_state_detects_nonempty_or_malformed_projection(tmp_path):
    storage = tmp_path / "storage"
    storage.mkdir()
    (storage / "operational_inputs.json").write_text(
        "not-json",
        encoding="utf-8",
    )
    (storage / "animal_operational_states.json").write_text(
        json.dumps([{"animal_id": "OLD-001"}]),
        encoding="utf-8",
    )

    assert verify_file_projection_zero_state(tmp_path) == {
        "animal_operational_states.json": 1,
        "operational_inputs.json": 1,
    }
