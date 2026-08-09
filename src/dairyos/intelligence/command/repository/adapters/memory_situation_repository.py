class MemorySituationRepository:


    def __init__(self):

        self.items = []


    def save(self, situation):

        self.items.append(
            situation
        )

        return situation
