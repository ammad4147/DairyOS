from ..models.knowledge_link import KnowledgeLink



class ClinicalReviewService:



    def review(

        self,

        indicators,

        knowledge_service

    ):

        conditions = []

        checks = []



        for indicator in indicators:

            matches = knowledge_service.find_by_indicator(

                indicator

            )


            for item in matches:

                conditions.append(

                    item.condition_name

                )


                checks.extend(

                    item.recommended_checks

                )



        return KnowledgeLink(

            indicators,

            list(set(conditions)),

            list(set(checks)),

            "REFERENCE"

        )
