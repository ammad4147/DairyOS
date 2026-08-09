from typing import List

from ..models.compliance_check import ComplianceCheck


class ComplianceService:
    """
    Tracks compliance checks.
    """

    def __init__(self):
        self.checks: List[ComplianceCheck] = []


    def record_check(
        self,
        check: ComplianceCheck,
    ) -> ComplianceCheck:

        self.checks.append(check)

        return check


    def get_checks(self):

        return list(self.checks)
