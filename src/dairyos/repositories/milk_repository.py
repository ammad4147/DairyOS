# src/dairyos/repositories/milk_repository.py
"""
Unified repository interface for milk and animal data.
"""

from abc import ABC, abstractmethod
from typing import Any


class MilkRepository(ABC):
    """
    Abstract methods required by the runtime.
    """

    @abstractmethod
    def add_animal(self, payload: dict[str, Any]) -> None: ...

    @abstractmethod
    def add_milk(self, payload: dict[str, Any]) -> None: ...

    @abstractmethod
    def feed_animal(self, payload: dict[str, Any]) -> None: ...

    @abstractmethod
    def list_animals(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def list_milk(self) -> list[dict[str, Any]]: ...
