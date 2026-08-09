from dairyos.feed import (
    FeedEvent,
    FeedOperationsBridge,
)



def test_feed_event_creation():

    event = FeedEvent(
        event_id="EV-001",
        event_type="FEED_RECEIVED",
        feed_id="SILAGE-001",
        quantity=500,
        actor="STORE_MANAGER",
    )


    assert event.event_id == "EV-001"
    assert event.event_type == "FEED_RECEIVED"



def test_publish_feed_event():

    bridge = FeedOperationsBridge()


    event = FeedEvent(
        event_id="EV-002",
        event_type="FEED_ISSUED",
        feed_id="CONCENTRATE-001",
        quantity=100,
        actor="FEED_OPERATOR",
    )


    bridge.publish(event)


    events = bridge.get_events()


    assert len(events) == 1
    assert events[0].feed_id == "CONCENTRATE-001"



def test_filter_feed_events():

    bridge = FeedOperationsBridge()


    bridge.publish(
        FeedEvent(
            event_id="EV-003",
            event_type="FEED_RECEIVED",
            feed_id="HAY-001",
            quantity=200,
            actor="STORE_MANAGER",
        )
    )


    bridge.publish(
        FeedEvent(
            event_id="EV-004",
            event_type="FEED_ISSUED",
            feed_id="HAY-001",
            quantity=50,
            actor="FEED_OPERATOR",
        )
    )


    received = bridge.get_events_by_type(
        "FEED_RECEIVED"
    )


    assert len(received) == 1
    assert received[0].quantity == 200
