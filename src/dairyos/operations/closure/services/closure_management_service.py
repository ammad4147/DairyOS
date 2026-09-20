

class ClosureManagementService:
    """
    Manages operational closure records.
    """


    def __init__(self):

        self.closures: list = []


    def create_closure(
        self,
        closure,
    ):

        self.closures.append(closure)

        return closure


    def active_closures(self):

        return [
            item
            for item in self.closures
            if item.status.value != "ACCEPTED"
        ]
