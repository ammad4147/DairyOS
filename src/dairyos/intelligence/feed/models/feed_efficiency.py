from dataclasses import dataclass


@dataclass
class FeedEfficiency:
    """Scientifically normalized feed-efficiency result.

    Compatibility fields are retained. ``feed_quantity`` represents DMI
    (kg DM) and ``milk_output`` represents ECM (kg ECM) for new calculations.
    """

    group_id: str
    feed_quantity: float
    milk_output: float
    efficiency: float
    status: str
    recommendation: str
    dmi_kg: float | None = None
    ecm_kg: float | None = None
    dim: int | None = None
    benchmark_good: float | None = None
    benchmark_attention: float | None = None
    data_quality: str = "HIGH"
