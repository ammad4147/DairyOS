from dairyos.operations.resilience.repositories.operational_exception_repository import (
    OperationalExceptionRepository,
)

from dairyos.operations.resilience.services.operational_exception_service import (
    OperationalExceptionService,
)



def test_exception_recording():

    repository = OperationalExceptionRepository()

    service = OperationalExceptionService(
        repository
    )


    exception = service.record_exception(
        category="late_entry",
        description="Feed entry delayed",
        severity="low",
        source="feeding_workflow",
    )


    assert exception.status == "open"

    assert exception.category == "late_entry"



def test_exception_resolution():

    repository = OperationalExceptionRepository()

    service = OperationalExceptionService(
        repository
    )


    exception = service.record_exception(
        category="missing_data",
        description="Milk record entered later",
        severity="medium",
        source="milk_collection",
    )


    resolved = service.resolve_exception(
        exception.exception_id
    )


    assert resolved.status == "resolved"

    assert resolved.resolved_at is not None
