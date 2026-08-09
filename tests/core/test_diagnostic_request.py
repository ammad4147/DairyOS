from dairyos.herd.health.services.diagnostic_request_service import (
    DiagnosticRequestService
)



def test_request_animal():

    result = DiagnosticRequestService().request(

        "HF-3002",

        "Milk Test",

        "Confirm suspected mastitis",

        "Veterinarian",

        "HIGH"

    )

    assert result.animal_id == "HF-3002"



def test_request_status():

    result = DiagnosticRequestService().request(

        "HF-3002",

        "Blood Test",

        "Check metabolic condition",

        "Vet",

        "MEDIUM"

    )

    assert result.status == "REQUESTED"



def test_request_priority():

    result = DiagnosticRequestService().request(

        "HF-3002",

        "Culture Test",

        "Confirm infection",

        "Vet",

        "HIGH"

    )

    assert result.priority == "HIGH"
