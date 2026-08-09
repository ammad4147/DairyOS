from dataclasses import dataclass, field


@dataclass(frozen=True)
class MilkProductionIntelligence:
    """
    Read-only milk production intelligence projection.

    Source:
        Verified FarmOperationalState milk facts.

    Does not:
        - create milk records
        - modify operational state
        - predict actual production
        - replace manual entry

    Provides:
        - production summary
        - checkpoint compliance
        - shift intelligence
        - operational signals
    """


    total_litres: float = 0.0


    shift_production: dict = field(
        default_factory=dict
    )


    shift_contribution: dict = field(
        default_factory=dict
    )


    average_per_milking_animal: float = 0.0


    expected_checkpoints: list = field(
        default_factory=list
    )


    completed_checkpoints: list = field(
        default_factory=list
    )


    missing_checkpoints: list = field(
        default_factory=list
    )


    production_status: str = "UNKNOWN"


    production_variance: float = 0.0


    production_analytics: dict = field(
        default_factory=dict
    )


    operational_signals: list = field(
        default_factory=list
    )


    notes: list = field(
        default_factory=list
    )



    @property
    def checkpoint_completion_rate(self):

        if not self.expected_checkpoints:

            return 0.0


        return (

            len(
                self.completed_checkpoints
            )

            /

            len(
                self.expected_checkpoints
            )

        ) * 100



    def is_complete(self):

        return (

            len(
                self.missing_checkpoints
            )

            ==

            0

        )



    def summary(self):

        return {

            "total_litres":
                self.total_litres,


            "shift_production":
                self.shift_production,


            "shift_contribution":
                self.shift_contribution,


            "average_per_milking_animal":
                self.average_per_milking_animal,


            "checkpoint_completion_rate":
                self.checkpoint_completion_rate,


            "missing_checkpoints":
                self.missing_checkpoints,


            "production_status":
                self.production_status,


            "production_variance":
                self.production_variance,


            "production_analytics":
                self.production_analytics,


            "operational_signals":
                self.operational_signals,


            "notes":
                self.notes,

        }
