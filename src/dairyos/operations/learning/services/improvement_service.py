from typing import List

from ..models.improvement_opportunity import ImprovementOpportunity
from ..models.operational_pattern import OperationalPattern


class ImprovementService:
    """
    Converts operational patterns into improvement opportunities.
    """

    def create_opportunities(
        self,
        patterns: List[OperationalPattern],
    ) -> List[ImprovementOpportunity]:

        return [
            ImprovementOpportunity(
                opportunity_id=f"IMP-{pattern.pattern_id}",
                title=f"Improve {pattern.name}",
                description=(
                    f"Review repeated "
                    f"{pattern.category} activity"
                ),
                priority=pattern.impact_level,
                related_pattern_id=pattern.pattern_id,
            )
            for pattern in patterns
        ]
