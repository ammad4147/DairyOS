from dataclasses import dataclass


@dataclass
class OperationalProcedure:
    """
    Defines a standard operating procedure.
    """

    procedure_id: str
    name: str
    department: str
    frequency: str
    required: bool
