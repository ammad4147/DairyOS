from dairyos.feed.intelligence.models import FeedSignal

from dairyos.feed.workflow.models import (
    FeedWorkflowRequest,
)


class FeedWorkflowService:
    """
    Converts Feed intelligence signals into operational requests.
    """


    def create_workflow_request(
        self,
        feed_signal: FeedSignal,
    ) -> FeedWorkflowRequest:


        priority = "NORMAL"

        if feed_signal.severity.value == "HIGH":
            priority = "URGENT"

        elif feed_signal.severity.value == "MEDIUM":
            priority = "HIGH"


        return FeedWorkflowRequest(
            animal_group=(
                feed_signal.animal_group
            ),
            issue_type=(
                feed_signal.signal_type.value
            ),
            severity=(
                feed_signal.severity.value
            ),
            priority=priority,
            recommended_action=(
                "Investigate feed delivery, "
                "ration consistency and intake causes"
            ),
        )
