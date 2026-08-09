from dairyos.milk.models.milking_session import MilkingSession


class MilkingSessionService:


    def __init__(self):

        self.sessions = [
            MilkingSession.MORNING,
            MilkingSession.AFTERNOON,
            MilkingSession.EVENING
        ]


    def get_sessions(self):

        return self.sessions
