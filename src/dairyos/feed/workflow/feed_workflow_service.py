from dairyos.feed.workflow.feed_workflow_event import (
    FeedWorkflowEvent,
)


class FeedWorkflowService:
    """
    Converts FeedOS signals into workflow requests.
    """

    def create_event(
        self,
        context: dict,
    ) -> FeedWorkflowEvent:

        return FeedWorkflowEvent(
            domain=context["domain"],
            animal_group=context["animal_group"],
            issue_type=context["signal_type"],
            severity=context["severity"],
            priority=context["severity"],
            recommended_action="Review feed intake variance.",
            requires_action=context["requires_attention"],
            message=context["message"],
        )


    def create_workflow_request(
        self,
        signal,
    ) -> FeedWorkflowEvent:

        severity = signal.severity.value

        if severity in (
            "HIGH",
            "CRITICAL",
        ):
            priority = "URGENT"

        elif severity == "MEDIUM":
            priority = "HIGH"

        else:
            priority = "NORMAL"

        return FeedWorkflowEvent(
            domain="FEED",
            animal_group=signal.animal_group,
            issue_type=signal.signal_type.value,
            severity=severity,
            priority=priority,
            recommended_action=(
                "Investigate feed delivery, "
                "inspect bunk management, "
                "review ration preparation, "
                "and verify animal health."
            ),
            requires_action=(
                severity != "LOW"
            ),
            message=signal.message,
        )
