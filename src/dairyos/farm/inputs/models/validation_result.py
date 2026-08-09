from dataclasses import dataclass


@dataclass
class OperationalInputValidationResult:
    """
    Result of operational input validation.
    """

    valid: bool

    message: str = ""

