from dairyos.intelligence.operations.orchestration.repository.execution_repository import (
    ExecutionRepository,
)


class MemoryExecutionRepository(ExecutionRepository):

    def __init__(self):
        self.records = []


    def save(self, record):

        self.records.append(record)

        return record


    def get_all(self):

        return self.records
