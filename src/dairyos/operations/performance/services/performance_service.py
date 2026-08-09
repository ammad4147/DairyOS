from typing import List

from ..models.performance_measurement import PerformanceMeasurement


class PerformanceService:
    """
    Records operational performance.
    """

    def __init__(self):
        self.measurements: List[PerformanceMeasurement] = []


    def record_measurement(
        self,
        measurement: PerformanceMeasurement,
    ) -> PerformanceMeasurement:

        self.measurements.append(measurement)

        return measurement


    def get_measurements(self):

        return list(self.measurements)
