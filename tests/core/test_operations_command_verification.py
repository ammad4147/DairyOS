from dairyos.operations.command_verification.models.verification_status import (
    VerificationStatus,
)
from dairyos.operations.command_verification.services.command_verification_service import (
    CommandVerificationService,
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
