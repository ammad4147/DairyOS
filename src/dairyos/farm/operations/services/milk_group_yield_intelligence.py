from dataclasses import dataclass, field


@dataclass(frozen=True)
class MilkGroupYieldIntelligence:
    """
    Read-only intelligence projection
    for milk production by animal group.

    Source:
        Verified milk operational records.

    Does not:
        - create milk records
        - modify herd facts
        - infer missing animals

    Provides:
        - group production
        - yield distribution
        - operational signals
    """


    group_production: dict = field(
        default_factory=dict
    )


    group_average_yield: dict = field(
        default_factory=dict
    )


    highest_producing_group: str | None = None


    lowest_producing_group: str | None = None


    signals: list = field(
        default_factory=list
    )


    def summary(self):

        return {

            "group_production":
                self.group_production,


            "group_average_yield":
                self.group_average_yield,


            "highest_producing_group":
                self.highest_producing_group,


            "lowest_producing_group":
                self.lowest_producing_group,


            "signals":
                self.signals,

        }
