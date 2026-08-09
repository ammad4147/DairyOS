from dairyos.feed.workflow import (
    FeedWorkflowService,
)


def test_feed_workflow_event_creation():

    service = FeedWorkflowService()

    context = {
        "domain": "FEED",
        "animal_group": "MILKING_COWS",
        "signal_type": "INTAKE_VARIANCE",
        "severity": "HIGH",
        "requires_attention": True,
        "message": "Feed variance detected",
    }

    event = service.create_event(
        context
    )

    assert event.domain == "FEED"
    assert event.animal_group == "MILKING_COWS"
    assert event.priority == "HIGH"
    assert event.requires_action is True
