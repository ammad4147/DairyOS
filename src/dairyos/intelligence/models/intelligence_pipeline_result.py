from dataclasses import dataclass, field
from datetime import datetime, timezone



@dataclass
class IntelligencePipelineResult:
    """
    Represents the complete output of an intelligence evaluation.

    Intelligence results are observations and recommendations.
    They do not modify operational facts.

    Provides dictionary compatibility for existing DairyOS consumers.
    """


    signals: list = field(
        default_factory=list
    )


    analysis: dict = field(
        default_factory=dict
    )


    recommendations: list = field(
        default_factory=list
    )


    evaluated_at: datetime = field(
        default_factory=lambda:
        datetime.now(timezone.utc)
    )


    execution_metadata: dict = field(
        default_factory=dict
    )



    def __getitem__(
        self,
        key,
    ):

        return getattr(
            self,
            key,
        )



    def __contains__(
        self,
        key,
    ):

        return hasattr(
            self,
            key,
        )



    def get(
        self,
        key,
        default=None,
    ):

        return getattr(
            self,
            key,
            default,
        )



    def keys(
        self,
    ):

        return [

            "signals",

            "analysis",

            "recommendations",

            "evaluated_at",

            "execution_metadata",

        ]



    def to_dict(
        self,
    ):

        return {

            "signals":
                self.signals,

            "analysis":
                self.analysis,

            "recommendations":
                self.recommendations,

            "evaluated_at":
                self.evaluated_at,

            "execution_metadata":
                self.execution_metadata,

        }
