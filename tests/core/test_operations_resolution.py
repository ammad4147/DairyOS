from datetime import datetime


from dairyos.operations.resolution.models.operational_resolution import (
    OperationalResolution,
)

from dairyos.operations.resolution.models.resolution_status import (
    ResolutionStatus,
)

from dairyos.operations.resolution.services.resolution_management_service import (
    ResolutionManagementService,
)

from dairyos.operations.resolution.services.resolution_verification_service import (
    ResolutionVerificationService,
)



def test_create_resolution():

    service = ResolutionManagementService()


    resolution = OperationalResolution(
        resolution_id="RES-001",
        issue_reference="ESC-001",
        action_taken="Completed corrective feeding schedule",
        assigned_to="Farm Supervisor",
        created_at=datetime.now(),
    )


    service.create_resolution(resolution)


    assert len(service.active_resolutions()) == 1



def test_verify_resolution():

    resolution = OperationalResolution(
        resolution_id="RES-002",
        issue_reference="TASK-002",
        action_taken="Repair completed",
        assigned_to="Technician",
        created_at=datetime.now(),
    )


    service = ResolutionVerificationService()


    service.verify(resolution)


    assert resolution.status == ResolutionStatus.VERIFIED
