from dairyos.intelligence.operations.orchestration.repository.assignment_repository import (
    AssignmentRepository,
)


class MemoryAssignmentRepository(AssignmentRepository):

    def __init__(self):
        self.assignments = []


    def save(self, assignment):

        self.assignments.append(assignment)

        return assignment


    def get_all(self):

        return self.assignments
