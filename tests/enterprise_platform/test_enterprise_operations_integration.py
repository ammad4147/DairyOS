from dairyos.platform.readiness.services.readiness_service import (
    ReadinessService,
)



from dairyos.platform.audit.services.audit_service import (
    AuditService,
)



from dairyos.platform.timeline.services.timeline_service import (
    TimelineService,
)



from dairyos.platform.decision.services.decision_service import (
    DecisionService,
)



from dairyos.platform.decision.models.decision_context import (
    DecisionContext,
)



def test_enterprise_readiness():

    service = ReadinessService()


    service.register(
        "event_fabric"
    )


    service.register(
        "workflow"
    )


    service.register(
        "security"
    )


    report = service.validate()


    assert report.ready is True



def test_decision_pipeline():

    context = DecisionContext(

        subject_type="animal",

        subject_id="1001",

        observation="milk decline",

        evidence=[

            "reduced intake",

            "production drop",

        ],

        risk_level="medium",

    )


    decision = DecisionService().evaluate(
        context
    )


    assert decision.confidence > 0



def test_timeline_and_audit():

    timeline = TimelineService()

    audit = AuditService()


    assert timeline.events == []


    assert audit.records == []

