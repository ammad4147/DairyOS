from dairyos.operations.command_verification.services.command_verification_service import (
    CommandVerificationService,
)

from dairyos.operations.command_verification.services.verification_analysis_service import (
    VerificationAnalysisService,
)

from dairyos.operations.command_verification.models.verification_status import (
    VerificationStatus,
)



def test_successful_command_verification():

    service = CommandVerificationService()


    verification = service.verify(
        "VER-001",
        "EXEC-001",
        True,
        "Task completed successfully",
    )


    assert verification.status == VerificationStatus.VERIFIED



def test_failed_command_requires_followup():

    service = CommandVerificationService()


    verification = service.verify(
        "VER-002",
        "EXEC-002",
        False,
        "Expected result not achieved",
    )


    analyzer = VerificationAnalysisService()


    assert analyzer.requires_followup(verification) is True
