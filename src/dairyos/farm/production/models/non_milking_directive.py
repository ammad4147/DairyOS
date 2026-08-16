from __future__ import annotations

from enum import Enum


class NonMilkingDirective(str, Enum):
    NONE = "NONE"
    TEMPORARY_NON_MILKING = "TEMPORARY_NON_MILKING"
    MILK_SEPARATELY = "MILK_SEPARATELY"
    PERMANENT_NON_MILKING = "PERMANENT_NON_MILKING"

    @property
    def is_outside_active_milking_herd(self) -> bool:
        return self is not NonMilkingDirective.NONE

    @property
    def expects_milk(self) -> bool:
        return self is NonMilkingDirective.MILK_SEPARATELY
