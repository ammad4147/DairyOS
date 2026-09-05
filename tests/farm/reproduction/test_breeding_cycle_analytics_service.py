from types import SimpleNamespace
from datetime import datetime, timezone

from dairyos.farm.reproduction.services.breeding_cycle_analytics_service import (
    BreedingAnalyticsService,
    BreedingCycleProjectionService,
)


def ev(animal, kind, day, result="RECORDED", semen=None, tech="Tech"):
    return SimpleNamespace(
        record_id=f"{animal}-{kind}-{day}",
        animal_id=animal,
        event_type=kind,
        result=result,
        semen_or_bull=semen,
        technician=tech,
        notes=None,
        timestamp=datetime.fromisoformat(day + "T00:00:00").replace(tzinfo=timezone.utc),
    )


def test_cycle_closure_and_restart_after_calving_abortion_negative_pd():
    records = [
        ev("A1","insemination","2025-01-01",semen="Conventional — SIRE-1"),
        ev("A1","pregnancy_confirmed","2025-02-01","confirmed"),
        ev("A1","calving","2025-10-11"),
        ev("A1","insemination","2026-01-10",semen="Conventional — SIRE-2"),
        ev("A1","pregnancy_confirmed","2026-02-10","confirmed"),
        ev("A1","abortion","2026-03-01","ABORTED"),
        ev("A1","insemination","2026-04-01",semen="Sexed Semen (90% Female) — SIRE-3"),
        ev("A1","pregnancy_negative","2026-05-01","open"),
        ev("A1","insemination","2026-06-01",semen="Conventional — SIRE-4"),
    ]
    cycles = BreedingCycleProjectionService.project(records)
    assert [c["cycle_number"] for c in cycles] == [1,2,3,4]
    assert [c["status"] for c in cycles] == [
        "CLOSED_CALVING","CLOSED_ABORTION","CLOSED_NOT_PREGNANT","ACTIVE_INSEMINATED"
    ]
    assert cycles[-1]["sire_code"] == "SIRE-4"
    current = BreedingCycleProjectionService.current_by_animal(cycles)
    assert current["A1"]["cycle_id"].endswith("C004")


def test_analytics_separates_animal_pattern_from_sire_pattern_with_evidence():
    records = []
    for i, animal in enumerate(("A1","A2","A3"), start=1):
        day=f"2026-01-0{i}"
        records += [
            ev(animal,"insemination",day,semen="Conventional — BAD-SIRE"),
            ev(animal,"pregnancy_negative",f"2026-02-0{i}","open"),
        ]
    for i, animal in enumerate(("B1","B2","B3"), start=1):
        records += [
            ev(animal,"insemination",f"2026-03-0{i}",semen="Conventional — GOOD-SIRE"),
            ev(animal,"pregnancy_confirmed",f"2026-04-0{i}","confirmed"),
            ev(animal,"calving",f"2026-12-0{i}"),
        ]

    cycles=BreedingCycleProjectionService.project(records)
    analytics=BreedingAnalyticsService.summarize(cycles)
    bad=next(row for row in analytics["by_sire"] if row["key"]=="BAD-SIRE")
    good=next(row for row in analytics["by_sire"] if row["key"]=="GOOD-SIRE")
    assert bad["conception_rate_percent"] == 0.0
    assert good["conception_rate_percent"] == 100.0
    signal=next(s for s in analytics["signals"] if s["dimension"]=="SIRE" and s["key"]=="BAD-SIRE")
    assert signal["sample_size"] == 3
    assert len(signal["cycle_ids"]) == 3
    assert set(signal["animal_ids"]) == {"A1","A2","A3"}


def test_small_sample_does_not_generate_failure_signal():
    records=[
        ev("A1","insemination","2026-01-01",semen="Conventional — ONE-OFF"),
        ev("A1","pregnancy_negative","2026-02-01","open"),
    ]
    analytics=BreedingAnalyticsService.summarize(BreedingCycleProjectionService.project(records))
    assert not [s for s in analytics["signals"] if s["key"]=="ONE-OFF"]
