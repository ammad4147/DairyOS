from dairyos.app import app


def _paths() -> set[str]:
    return {route.path for route in app.routes}


def test_cross_domain_operational_capability_routes_are_registered():
    paths = _paths()
    expected = {
        "/farm/animals/{animal_id}/passport",
        "/farm/animals/{animal_id}/reproduction",
        "/farm/youngstock",
        "/farm/kpis",
        "/farm/heat-stress",
        "/farm/heat-stress/observations",
        "/farm/welfare/kpis",
        "/farm/sops",
        "/farm/nutrition/rations",
        "/farm/finance/cost-of-production",
        "/farm/finance/reconciliation",
        "/farm/reference-data",
    }
    assert expected <= paths


def test_backup_and_recovery_utility_exists():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    utility = root / "scripts" / "database_backup.py"
    runbook = root / "docs" / "operations" / "DISASTER_RECOVERY.md"
    assert utility.exists()
    assert runbook.exists()
    utility_text = utility.read_text(encoding="utf-8")
    assert "pg_dump" in utility_text
    assert "pg_restore" in utility_text
    assert "Recovery acceptance criteria" in runbook.read_text(encoding="utf-8")
