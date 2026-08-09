from dairyos.farm.operations.gateway.operations_event_gateway import (
    OperationsEventGateway,
)


class OperationsTimelineService:
    """
    Farm operational timeline.

    Converts operational events into
    timeline-safe dictionary records.
    """


    def __init__(
        self,
        gateway=None,
    ):

        self.gateway = (
            gateway
            if gateway is not None
            else OperationsEventGateway()
        )

        self.timeline_events = []



    def record(
        self,
        event,
    ):

        published = (
            self.gateway
            .publish(event)
        )


        timeline_record = {

            "event_type": published["event_type"],

            "animal_id": published["animal_id"],

            "operator": published.get(
                "operator"
            ),

            "timestamp": published.get(
                "timestamp"
            ),

            "payload": published.get(
                "payload",
                {},
            ),

        }


        self.timeline_events.append(
            timeline_record
        )


        return timeline_record



    def get_timeline(
        self,
    ):

        return self.timeline_events
