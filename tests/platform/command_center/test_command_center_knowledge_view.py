from dairyos.platform.command_center.knowledge.knowledge_view_service import (
    KnowledgeViewService,
)



def test_command_center_knowledge_summary():


    service = KnowledgeViewService()



    summary = service.build_summary(

        subject="milk decline",

        findings=[

            "feed change",

            "health event"

        ],

        confidence=0.78,

    )



    assert summary.subject == "milk decline"


    assert len(summary.findings) == 2


    assert summary.confidence == 0.78

