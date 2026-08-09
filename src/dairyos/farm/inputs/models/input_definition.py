from dataclasses import dataclass, field


@dataclass
class OperationalInputDefinition:
    """
    Enterprise operational input contract.

    Defines the accepted structure, normalization rules,
    governance requirements, intelligence behaviour,
    analytics outputs, notifications, decisions,
    and data quality expectations of a farm operational input.
    """


    input_type: str

    name: str

    description: str


    #
    # Contract behaviour
    #

    required: bool = True


    required_fields: list[str] = field(
        default_factory=list
    )


    optional_fields: list[str] = field(
        default_factory=list
    )


    field_aliases: dict[str, list[str]] = field(
        default_factory=dict
    )


    #
    # Platform capabilities
    #

    analytics_enabled: bool = True


    notification_enabled: bool = True


    governance_required: bool = True


    normalization_enabled: bool = True



    #
    # Intelligence contract
    #

    analytics_metrics: list[str] = field(
        default_factory=list
    )


    notification_rules: list[str] = field(
        default_factory=list
    )


    decision_dependencies: list[str] = field(
        default_factory=list
    )


    #
    # Data quality contract
    #

    data_quality_rules: list[str] = field(
        default_factory=list
    )
