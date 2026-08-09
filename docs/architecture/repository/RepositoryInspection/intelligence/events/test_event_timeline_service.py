from datetime import datetime, timezone, timedelta


from dairyos.intelligence.persistence.repositories.adapters.memory_event_repository import (
    MemoryEventRepository,
)

from dairyos.intelligence.persistence.models.intelligence_event import (
    IntelligenceEvent,
)

from dairyos.intelligence.events.services.event_query_service import (
    EventQueryService,
)

from dairyos.intelligence.events.services.event_timeline_service import (
    EventTimelineService,
)



def test_event_timeline_groups_correlated_events():

    repository = MemoryEventRepository()


    first = IntelligenceEvent(
        event_type="decision_created",
        source="decision_engine",
        payload={},
    )


    second = IntelligenceEvent(
        event_type="execution_started",
        source="execution_engine",
        payload={},
    )


    correlation = first.correlation_id

    second.correlation_id = correlation


    repository.save_event(
        first
    )

    repository.save_event(
        second
    )


    query = EventQueryService(
        repository
    )


    timeline = EventTimelineService(
        query
    )


    result = timeline.get_timeline(
        correlation
    )


    assert len(result) == 2

    assert result[0].correlation_id == (
        correlation
    )

    assert result[1].correlation_id == (
        correlation
    )
