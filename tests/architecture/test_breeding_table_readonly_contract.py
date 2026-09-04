from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_breeding_register_has_no_status_mutation_column():
    source = text("src/DairyOS.Web/src/components/BreedingTab.tsx")

    assert "Current Stage" not in source
    assert "Status is changed only through the breeding entry forms." not in source
    assert "handleStatusChange" not in source
    assert "statusOptionsForState" not in source
    assert 'title="Change current reproductive status.' not in source
    assert (
        "['Animal & Breeding Readiness','Insemination Date & Sire','Semen Type',"
        "'Pregnancy & Calving Timeline','Clinical Notes']"
    ) in source


def test_breeding_entry_form_is_the_authoritative_lifecycle_surface():
    source = text("src/DairyOS.Web/src/components/BreedingTab.tsx")

    assert "Record Reproduction & Gestation Event" in source
    assert "Insemination (AI)" in source
    assert "Pregnancy Check / Review (PD)" in source
    assert "Calving" in source
    assert "Pregnancy Loss" in source
    assert "Miscarriage" in source
    assert "Aborted Pregnancy" in source
    assert "Save Breeding Entry" in source
    assert "await postJson('/farm/breeding'" in source


def test_breeding_form_candidate_lists_follow_manual_lifecycle_sequence():
    source = text("src/DairyOS.Web/src/components/BreedingTab.tsx")

    # PD is available after insemination and remains available after a positive
    # declaration so an operator can manually reconfirm or revise pregnancy.
    assert (
        "['INSEMINATED','BRED','PREGNANT'].includes(norm(byId.get(a.id)?.state))"
        in source
    )
    assert "Pregnancy Check / Review (PD)" in source
    assert "Negative (Revise to Not Pregnant / Open)" in source
    assert (
        "No inseminated or confirmed-pregnant animals currently available for "
        "pregnancy diagnosis/review"
    ) in source

    # Calving and explicit pregnancy-loss entries remain restricted to animals
    # whose current manual state is confirmed pregnant.
    assert "(eventType==='CALVING'||eventType==='LOSS')" in source
    assert "norm(byId.get(a.id)?.state)==='PREGNANT'" in source
    assert "No confirmed pregnant animals currently awaiting calving" in source
    assert "No confirmed pregnant animals currently available for pregnancy-loss entry" in source


def test_breeding_outcome_analytics_include_manual_outcomes():
    source = text("src/DairyOS.Web/src/components/BreedingTab.tsx")

    assert "Insemination Success Analytics" in source
    assert "Pregnancy Outcome Analytics" in source
    assert "Confirmed Pregnancies" in source
    assert "Negative PD Results" in source
    assert "Calvings" in source
    assert "Miscarriages" in source
    assert "Abortions" in source
    assert "Pregnancy Loss Rate" in source
