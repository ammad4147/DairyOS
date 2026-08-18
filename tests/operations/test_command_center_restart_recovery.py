from types import SimpleNamespace

from dairyos.domain.events import Event
from dairyos.farm.command_center.services.operational_command_center_service import (
    OperationalCommandCenterService,
)


def _service(events):
    state = SimpleNamespace(
        health_state={
            "TD-001": {
                "animal_id": "TD-001",
                "observation": "Reduced appetite",
                "severity": "HIGH",
            }
        },
        health_alerts=[],
        exceptions=[],
        open_tasks=[],
        schedule_state=None,
    )

    state.summary = lambda: state

    health = SimpleNamespace(
        generate_snapshot=lambda **kwargs: SimpleNamespace(
            health_status="OK",
            operational_score=100,
            active_decisions=kwargs.get("active_decisions", 0),
            pending_actions=kwargs.get("pending_actions", 0),
            tracked_outcomes=0,
            learning_signals=0,
            owner_attention_required=False,
        )
    )

    return OperationalCommandCenterService(
        operational_state_service=SimpleNamespace(
            get_state=lambda: state
        ),
        operations_health_service=health,
        event_publisher=events.append,
    )


def test_command_center_decisions_and_actions_survive_restore():
    events = []

    first = _service(events)

    recommendation = {
        "type": "health",
        "priority": "HIGH",
        "animal_id": "TD-001",
        "action": "review_health_observation",
        "title": "Review health observation",
        "details": {
            "animal_id": "TD-001",
            "observation": "Reduced appetite",
            "severity": "HIGH",
        },
        "source": "health",
        "owner_action_required": True,
    }

    key = first._condition_key(recommendation)
    decision = first._create_decision(
        key,
        recommendation,
    )

    first._decisions[key] = decision
    first._sync_actions()

    assert len(first.operational_action_service.get_actions()) == 1

    first.acknowledge_decision(
        decision.decision_id,
        "Veterinarian",
    )

    action = (
        first.operational_action_service
        .get_actions()[0]
    )

    first.update_action(
        action.action_id,
        "IN_PROGRESS",
        "Veterinarian",
    )

    second = _service([])

    second.restore_from_events(events)

    restored_decision = (
        second._find_decision(
            decision.decision_id
        )
    )

    restored_action = (
        second.operational_action_service
        .get_actions()[0]
    )

    assert restored_decision.status == "ACKNOWLEDGED"
    assert restored_decision.owner == "Veterinarian"

    assert restored_action.action_id == action.action_id
    assert restored_action.status.status == "IN_PROGRESS"
    assert (
        restored_action.assignment.assigned_to
        == "Veterinarian"
    )


def test_restore_is_idempotent():
    events = []

    service = _service(events)

    recommendation = {
        "type": "health",
        "priority": "HIGH",
        "animal_id": "TD-001",
        "action": "review_health_observation",
        "title": "Review health observation",
        "details": {
            "animal_id": "TD-001",
            "observation": "Reduced appetite",
            "severity": "HIGH",
        },
        "source": "health",
        "owner_action_required": True,
    }

    key = service._condition_key(
        recommendation
    )
    decision = service._create_decision(
        key,
        recommendation,
    )
    service._decisions[key] = decision
    service._sync_actions()

    replay = _service([])
    replay.restore_from_events(events)
    replay.restore_from_events(events)

    assert len(replay._decisions) == 1
    assert len(
        replay.operational_action_service.get_actions()
    ) == 1
