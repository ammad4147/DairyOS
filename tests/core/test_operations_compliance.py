from dairyos.operations.compliance.models.operational_procedure import (
    OperationalProcedure,
)

from dairyos.operations.compliance.services.procedure_service import (
    ProcedureService,
)

from dairyos.operations.compliance.models.compliance_check import (
    ComplianceCheck,
)

from dairyos.operations.compliance.services.compliance_service import (
    ComplianceService,
)


def test_procedure_registration():

    service = ProcedureService()

    service.register_procedure(
        OperationalProcedure(
            procedure_id="SOP-001",
            name="Morning Milking",
            department="Production",
            frequency="Daily",
            required=True,
        )
    )

    assert len(service.get_procedures()) == 1


def test_compliance_record():

    service = ComplianceService()

    service.record_check(
        ComplianceCheck(
            check_id="CHK-001",
            procedure_id="SOP-001",
            status="COMPLIANT",
            completion_percentage=100.0,
        )
    )

    assert service.get_checks()[0].status == "COMPLIANT"
