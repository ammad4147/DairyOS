"""
Legacy DairyOS Farm compatibility entity.

This module is retained for import compatibility only.
Production PostgreSQL persistence authority is:

    dairyos.data.database.models.farm_model.FarmModel

This compatibility class must not attach a second ``farms`` table to
DairyOS SQLAlchemy Base.metadata.
"""

from dataclasses import dataclass


@dataclass
class Farm:
    id: int | None = None
    name: str = ""
    location: str = ""
