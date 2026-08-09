from dataclasses import dataclass



@dataclass
class CopilotResponse:

    message: str

    confidence: float

    recommendations: list

