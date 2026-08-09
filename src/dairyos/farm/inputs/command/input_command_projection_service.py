class InputCommandProjectionService:
    """
    Provides command-layer projection
    of operational input intelligence.
    """

    def __init__(
        self,
        query_service=None,
        intelligence_service=None,
        notification_service=None,
        governance_service=None,
    ):

        self.query_service = query_service

        self.intelligence_service = (
            intelligence_service
        )

        self.notification_service = (
            notification_service
        )

        self.governance_service = (
            governance_service
        )



    def snapshot(
        self,
    ):

        return {

            "recent_inputs":
                self._recent_inputs(),

            "intelligence":
                self._intelligence(),

            "notifications":
                self._notifications(),

            "governance":
                self._governance(),

        }



    def _recent_inputs(
        self,
    ):

        if not self.query_service:

            return []


        return self.query_service.list_all()



    def _intelligence(
        self,
    ):

        if not self.intelligence_service:

            return {}


        return self.intelligence_service.summary()



    def _notifications(
        self,
    ):

        if not self.notification_service:

            return []


        return self.notification_service.list_notifications()



    def _governance(
        self,
    ):

        if not self.governance_service:

            return []


        return [
            record.__dict__
            for record in
            self.governance_service.list_records()
        ]
