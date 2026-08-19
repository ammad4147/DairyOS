from types import SimpleNamespace

from dairyos.farm.command_center.services.attention_queue_service import (
    AttentionQueueService,
)


class FakeFindingRepository:
    def __init__(self, findings):
        self.findings = list(findings)

    def get_open(self):
        return list(self.findings)


def test_attention_queue_surfaces_persisted_critical_finding():
    finding = SimpleNamespace(
        source_module="MILK",
        subject_id="TD-001",
        severity="CRITICAL",
        title="Milk withdrawal breach",
        detail="Milk from treated animal must not enter saleable stock.",
        status="RAISED",
    )

    service = AttentionQueueService(
        operational_finding_repository=FakeFindingRepository([finding])
    )

    farm_state = SimpleNamespace(
        health_state={},
        health_alerts=[],
    )

    items = service.build(farm_state=farm_state)

    assert len(items) == 1
    assert items[0].priority == "CRITICAL"
    assert items[0].area == "MILK"
    assert items[0].animal_id == "TD-001"
    assert "Milk withdrawal breach" in items[0].message


def test_attention_queue_ignores_resolved_findings_when_repository_filters_open():
    resolved_finding = SimpleNamespace(
        source_module="HEALTH",
        subject_id="TD-002",
        severity="HIGH",
        title="Resolved health issue",
        detail="Already closed.",
        status="RESOLVED",
    )

    service = AttentionQueueService(
        operational_finding_repository=FakeFindingRepository([])
    )

    farm_state = SimpleNamespace(
        health_state={},
        health_alerts=[],
    )

    items = service.build(farm_state=farm_state)

    assert items == []
    assert resolved_finding.status == "RESOLVED"


def test_attention_queue_deduplicates_health_state_and_finding_for_same_condition():
    finding = SimpleNamespace(
        source_module="HEALTH",
        subject_id="TD-003",
        severity="HIGH",
        title="Reduced appetite",
        detail="Reduced appetite",
        status="RAISED",
    )

    service = AttentionQueueService(
        operational_finding_repository=FakeFindingRepository([finding])
    )

    farm_state = SimpleNamespace(
        health_state={
            "TD-003": {
                "animal_id": "TD-003",
                "severity": "HIGH",
                "observation": "Reduced appetite",
            }
        },
        health_alerts=[],
    )

    items = service.build(farm_state=farm_state)

    assert len(items) == 1
    assert items[0].area == "HEALTH"
    assert items[0].animal_id == "TD-003"
