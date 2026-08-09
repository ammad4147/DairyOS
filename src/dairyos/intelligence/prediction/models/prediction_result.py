from dataclasses import dataclass


@dataclass
class PredictionResult:
    """
    Represents a deterministic intelligence prediction.

    Future extensions:

    - machine learning confidence
    - probability models
    - time-series forecasting
    """


    category: str

    prediction: str

    confidence: float

    horizon: str
