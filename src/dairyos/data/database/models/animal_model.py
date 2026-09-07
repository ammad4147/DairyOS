"""
Legacy compatibility alias.

Canonical DairyOS animal persistence authority:

    dairyos.data.models.animal.Animal

This module must not declare a second physical ``animals`` table.
"""

from dairyos.data.models.animal import Animal

AnimalModel = Animal

__all__ = ["AnimalModel"]
