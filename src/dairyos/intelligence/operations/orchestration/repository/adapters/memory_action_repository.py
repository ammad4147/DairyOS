from dairyos.intelligence.operations.orchestration.repository.action_repository import (
    ActionRepository,
)


class MemoryActionRepository(ActionRepository):

    def __init__(self):
        self.actions = []

    def save(self, action):

        self.actions.append(action)

        return action


    def get_all(self):

        return self.actions
