from dairyos.intelligence.persistence.repositories.adapters.memory_event_repository import (
    MemoryEventRepository,
)

from dairyos.intelligence.persistence.models.intelligence_event import (
    IntelligenceEvent,
)

from dairyos.intelligence.events.services.event_query_service import (
    EventQueryService,
)

from dairyos.intelligence.events.services.enterprise_replay_service import (
    EnterpriseReplayService,
)



def test_enterprise_replay_returns_entity_history():

    repository = MemoryEventRepository()


    repository.save_event(
        IntelligenceEvent(
            event_type="autonomous_cycle_completed",
            source="autonomous_intelligence",
            payload={
                "entity_id": "cycle-001",
                "status": "completed",
            },
        )
    )


    query = EventQueryService(
        repository
    )


    replay = EnterpriseReplayService(
        query
    )


    history = replay.replay_entity(
        "cycle-001"
    )


    assert len(history) == 1

    assert history[0]["event_type"] == (
        "autonomous_cycle_completed"
    )

    assert history[0]["payload"]["status"] == (
        "completed"
    )
