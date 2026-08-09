from typing import List

from ..models.operational_procedure import OperationalProcedure


class ProcedureService:
    """
    Manages operational procedures.
    """

    def __init__(self):
        self.procedures: List[OperationalProcedure] = []


    def register_procedure(
        self,
        procedure: OperationalProcedure,
    ) -> OperationalProcedure:

        self.procedures.append(procedure)

        return procedure


    def get_procedures(self):

        return list(self.procedures)
