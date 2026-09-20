from __future__ import annotations

from pathlib import Path

from dairyos.windows import supervisor

RETIRED_SUPERVISOR_MARKERS = (
    "process_pending_installation_choice",
    "queue_installation_choice",
    "--lifecycle-choice",
    "--choice-mode",
    "--backup-path",
)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_installation_choice_module_is_retired():
    module = (
        _repository_root()
        / "src"
        / "dairyos"
        / "windows"
        / "installation_choice.py"
    )

    assert not module.exists()


def test_supervisor_has_no_installation_choice_processing_api():
    assert not hasattr(supervisor, "process_pending_installation_choice")
    assert not hasattr(supervisor, "queue_installation_choice")


def test_supervisor_source_has_no_retired_installation_choice_cli():
    source = (
        _repository_root()
        / "src"
        / "dairyos"
        / "windows"
        / "supervisor.py"
    ).read_text(encoding="utf-8")

    for marker in RETIRED_SUPERVISOR_MARKERS:
        assert marker not in source


def test_python_production_tree_has_no_pending_installation_choice_contract():
    source_root = _repository_root() / "src" / "dairyos"

    forbidden = (
        "pending-installation-choice",
        "dairyos.windows.installation_choice",
        "FarmLaunchMode",
        "require_explicit_mode",
        "validate_new_installation",
        "validate_existing_installation",
        "choose_existing_backup",
    )

    hits: list[str] = []

    for path in source_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for marker in forbidden:
            if marker in text:
                hits.append(f"{path.relative_to(_repository_root())}: {marker}")

    assert hits == []
