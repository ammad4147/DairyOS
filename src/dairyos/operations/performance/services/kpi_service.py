from typing import List

from ..models.operational_kpi import OperationalKPI


class KPIService:
    """
    Manages operational KPIs.
    """

    def __init__(self):
        self.kpis: List[OperationalKPI] = []


    def register_kpi(
        self,
        kpi: OperationalKPI,
    ) -> OperationalKPI:

        self.kpis.append(kpi)

        return kpi


    def get_kpis(self):

        return list(self.kpis)
