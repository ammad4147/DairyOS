from dairyos.core.events.models import DairyEvent
from dairyos.core.events.services.publisher import EventPublisher

from dairyos.core.workflows.rules.engine import WorkflowEngine
from dairyos.core.workflows.rules.animal_rules import calving_rule



def test_event_publish():

    publisher = EventPublisher()

    event = DairyEvent(
        event_type="CALVING_COMPLETED",
        source="HerdOS",
        data={
            "animal_id":101
        }
    )

    result = publisher.publish(event)

    assert result.event_type == "CALVING_COMPLETED"



def test_workflow_rule():

    engine = WorkflowEngine()

    engine.add_rule(calving_rule)

    event = DairyEvent(
        event_type="CALVING_COMPLETED",
        source="HerdOS",
        data={}
    )

    result = engine.evaluate(event)

    assert result[0]["action"] == "CREATE_CALF_RECORD"
