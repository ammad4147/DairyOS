from datetime import datetime


from dairyos.herd.health.models.treatment_record import (
    TreatmentRecord
)

from dairyos.herd.health.models.treatment_response import (
    TreatmentResponse
)

from dairyos.herd.health.models.recovery_outcome import (
    RecoveryOutcome
)

from dairyos.herd.health.services.treatment_service import (
    TreatmentService
)

from dairyos.herd.health.services.recovery_monitor_service import (
    RecoveryMonitorService
)



def test_create_treatment():

    treatment = TreatmentRecord(

        "HF-14001",

        "Mastitis",

        "Medication",

        "Veterinary prescribed",

        "As directed",

        "Vet",

        datetime.now(),

        "ACTIVE"

    )


    result = TreatmentService().create(

        treatment

    )


    assert result.status == "ACTIVE"



def test_response_recording():

    service = RecoveryMonitorService()


    response = TreatmentResponse(

        "HF-14002",

        "TR-01",

        "Milk improving",

        "POSITIVE",

        datetime.now()

    )


    result = service.record_response(

        response

    )


    assert result.response_status == "POSITIVE"



def test_recovery_outcome():

    service = RecoveryMonitorService()


    outcome = RecoveryOutcome(

        "HF-14003",

        "Recovered",

        "COMPLETE",

        "Vet",

        datetime.now()

    )


    result = service.record_outcome(

        outcome

    )


    assert result.recovery_status == "COMPLETE"
