from typing import List

from ..models.learning_signal import LearningSignal
from ..models.operational_pattern import OperationalPattern


class PatternDetectionService:
    """
    Detects repeated operational behaviour.
    """

    def detect_patterns(
        self,
        signals: List[LearningSignal],
    ) -> List[OperationalPattern]:

        patterns = []

        categories = {}

        for signal in signals:
            categories.setdefault(
                signal.category,
                [],
            ).append(signal)

        for category, items in categories.items():

            if len(items) >= 2:

                patterns.append(
                    OperationalPattern(
                        pattern_id=f"PAT-{category}",
                        name=f"Repeated {category} activity",
                        category=category,
                        occurrence_count=len(items),
                        impact_level=items[-1].impact_level,
                        signal_ids=[
                            item.signal_id
                            for item in items
                        ],
                    )
                )

        return patterns
