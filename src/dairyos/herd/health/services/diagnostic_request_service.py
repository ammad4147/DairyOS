from datetime import datetime

from ..models.diagnostic_request import DiagnosticRequest



class DiagnosticRequestService:



    def request(

        self,

        animal_id,

        test_type,

        reason,

        requested_by,

        priority

    ):

        return DiagnosticRequest(

            animal_id=animal_id,

            test_type=test_type,

            reason=reason,

            requested_by=requested_by,

            priority=priority,

            status="REQUESTED",

            requested_at=datetime.now()

        )
