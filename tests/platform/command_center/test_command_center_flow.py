from dairyos.platform.command_center.alerts.models.command_alert import (
    CommandAlert,
)

from dairyos.platform.command_center.alerts.services.alert_service import (
    AlertService,
)


from dairyos.platform.command_center.priorities.services.prioritization_service import (
    PrioritizationService,
)


from dairyos.platform.command_center.governance.services.governance_service import (
    GovernanceService,
)


from dairyos.platform.command_center.timeline.models.timeline_event import (
    TimelineEvent,
)


from dairyos.platform.command_center.timeline.services.timeline_service import (
    TimelineService,
)


from dairyos.platform.command_center.learning.models.learning_feedback import (
    LearningFeedback,
)


from dairyos.platform.command_center.learning.services.feedback_service import (
    FeedbackService,
)



def test_command_center_operational_cycle():

    alerts = AlertService()


    alert = CommandAlert(

        title="Milk production decline",

        category="milk_production",

        severity="critical",

        entity_type="cow_group",

        entity_id="group_a",

    )


    alerts.create(alert)


    assert len(alerts.open_alerts()) == 1



    priorities = PrioritizationService()


    priority = priorities.calculate(

        severity="critical",

        impact="high",

        urgency="today",

    )


    assert priority.score > 0



    governance = GovernanceService()


    assert governance.authorize(

        "manager",

        "execute",

    )


    audit = governance.record_action(

        actor_id="manager",

        action="review_alert",

        entity_type="cow_group",

        entity_id="group_a",

        result="completed",

    )


    assert audit.result == "completed"



    timeline = TimelineService()


    event = TimelineEvent(

        event_type="alert",

        title="Milk production decline",

        entity_type="cow_group",

        entity_id="group_a",

        actor="manager",

        severity="critical",

    )


    timeline.record(event)


    assert len(timeline.latest()) == 1



    learning = FeedbackService()


    signal = LearningFeedback(

        source="command_center",

        signal_type="success",

        confidence=0.9,

        metadata={},

    )


    learning.record(signal)


    assert len(learning.all_feedback()) == 1

