class MemoryActionRepository:


    def __init__(self):

        self.items = []


    def save(self, action):

        self.items.append(
            action
        )

        return action
