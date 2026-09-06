from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SOURCE = (
    ROOT
    / "src/dairyos/data/database/database.py"
).read_text(encoding="utf-8")


def test_database_initialization_registers_health_case():
    assert (
        "from dairyos.data.models.health_case import"
        in SOURCE
    )
    assert "HealthCase" in SOURCE


def test_database_initialization_registers_operational_finding_lifecycle():
    assert (
        "from dairyos.data.models.operational_finding_lifecycle_event import"
        in SOURCE
    )
    assert "OperationalFindingLifecycleEvent" in SOURCE