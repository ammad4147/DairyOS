from dairyos.intelligence.integration.autonomous_replay_service import (
    AutonomousReplayService,
)

from dairyos.intelligence.persistence.services.history.intelligence_history_service import (
    IntelligenceHistoryService,
)

from dairyos.intelligence.persistence.repositories.adapters.memory_event_repository import (
    MemoryEventRepository,
)

from dairyos.intelligence.persistence.services.event_recorder import (
    EventRecorder,
)


def test_autonomous_replay_cycle():

    repository = MemoryEventRepository()

    recorder = EventRecorder(
        repository
    )


    recorder.record(
        event_type="autonomous_cycle_completed",
        source="autonomous_intelligence",
        payload={
            "cycle_id": "cycle-001",
            "status": "completed",
            "stages": [
                "prediction",
                "decision",
            ],
            "stage_count": 2,
        },
    )


    service = AutonomousReplayService(
        IntelligenceHistoryService(
            repository
        )
    )


    replay = service.replay_cycle(
        "cycle-001"
    )


    assert replay is not None

    assert replay["status"] == (
        "completed"
    )

    assert replay["stage_count"] == 2
