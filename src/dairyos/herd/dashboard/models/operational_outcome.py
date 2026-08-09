from dataclasses import dataclass



@dataclass
class OperationalOutcome:


    action: str

    result: str

    success: bool

    learning_note: str
