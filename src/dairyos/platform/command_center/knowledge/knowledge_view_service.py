from dairyos.platform.command_center.knowledge.knowledge_summary import (
    KnowledgeSummary,
)



class KnowledgeViewService:


    def build_summary(

        self,

        subject,

        findings,

        confidence,

    ):


        return KnowledgeSummary(

            subject=subject,

            findings=findings,

            confidence=confidence,

            explanation=(

                "Knowledge graph analysis completed"

            ),

        )

