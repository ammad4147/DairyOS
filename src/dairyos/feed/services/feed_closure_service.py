class FeedClosureService:


    REQUIRED_SESSIONS = {
        "MORNING",
        "AFTERNOON",
        "EVENING",
    }


    def validate_day(self, feeding_records):

        sessions = set()

        for record in feeding_records:

            if hasattr(record, "session"):
                sessions.add(record.session)

        return self.REQUIRED_SESSIONS.issubset(
            sessions
        )
