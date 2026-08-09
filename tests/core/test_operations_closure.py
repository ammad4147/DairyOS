from datetime import datetime


from dairyos.operations.closure.models.operational_closure import (
    OperationalClosure,
)

from dairyos.operations.closure.models.closure_status import (
    ClosureStatus,
)

from dairyos.operations.closure.services.closure_management_service import (
    ClosureManagementService,
)

from dairyos.operations.closure.services.closure_review_service import (
    ClosureReviewService,
)



def test_create_closure():

    service = ClosureManagementService()


    closure = OperationalClosure(
        closure_id="CLS-001",
        resolution_reference="RES-001",
        reviewed_by="Farm Manager",
        effectiveness_score=90,
        created_at=datetime.now(),
    )


    service.create_closure(closure)


    assert len(service.active_closures()) == 1



def test_accept_effective_closure():

    closure = OperationalClosure(
        closure_id="CLS-002",
        resolution_reference="RES-002",
        reviewed_by="Owner",
        effectiveness_score=95,
        created_at=datetime.now(),
    )


    service = ClosureReviewService()


    service.review(closure)


    assert closure.status == ClosureStatus.ACCEPTED
