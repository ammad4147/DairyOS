from dataclasses import dataclass, field


@dataclass(frozen=True)
class MilkingSessionComplianceIntelligence:
    """
    Read-only intelligence projection for
    milking execution compliance.

    Source:
        Verified milk operational entries
        compared against entered schedule expectations.

    Does not:
        - create missing sessions
        - modify milk records
        - complete operational tasks

    Provides:
        - session compliance
        - missing session awareness
        - execution signals
    """


    expected_sessions: list = field(
        default_factory=list
    )


    completed_sessions: list = field(
        default_factory=list
    )


    missing_sessions: list = field(
        default_factory=list
    )


    compliance_percentage: float = 0.0


    compliance_status: str = "UNKNOWN"


    signals: list = field(
        default_factory=list
    )


    def summary(self):

        return {

            "expected_sessions":
                self.expected_sessions,


            "completed_sessions":
                self.completed_sessions,


            "missing_sessions":
                self.missing_sessions,


            "compliance_percentage":
                self.compliance_percentage,


            "compliance_status":
                self.compliance_status,


            "signals":
                self.signals,

        }
