from ..models.executive_intelligence_summary import ExecutiveIntelligenceSummary



class ExecutiveIntelligenceSummaryService:



    def generate(

        self,

        farm_status,

        concern,

        recommendation,

        actions

    ):


        attention = (

            farm_status != "STABLE"

            or len(actions) > 0

        )


        return ExecutiveIntelligenceSummary(

            farm_status,

            concern,

            recommendation,

            actions,

            attention

        )



    def requires_owner_attention(

        self,

        summary

    ):


        return summary.owner_attention
