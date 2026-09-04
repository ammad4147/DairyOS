from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_breeding_register_current_stage_is_read_only():
    source = text("src/DairyOS.Web/src/components/BreedingTab.tsx")

    assert "Current Stage" in source
    assert "Status is changed only through the breeding entry forms." in source
    assert "handleStatusChange" not in source
    assert "statusOptionsForState" not in source
    assert 'title="Change current reproductive status.' not in source


def test_breeding_entry_form_remains_authoritative_entry_surface():
    source = text("src/DairyOS.Web/src/components/BreedingTab.tsx")

    assert "Record Reproduction & Gestation Event" in source
    assert "Insemination (AI)" in source
    assert "Pregnancy Check (PD)" in source
    assert "Calving" in source
    assert "Save Breeding Entry" in source
    assert "await postJson('/farm/breeding'" in source
