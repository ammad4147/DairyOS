# src/dairyos/repositories/milk_repository.py
"""
Unified repository interface for milk and animal data.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any

class MilkRepository(ABC):
    """
    Abstract methods required by the runtime.
    """

    @abstractmethod
    def add_animal(self, payload: Dict[str, Any]) -> None: ...

    @abstractmethod
    def add_milk(self, payload: Dict[str, Any]) -> None: ...

    @abstractmethod
    def feed_animal(self, payload: Dict[str, Any]) -> None: ...

    @abstractmethod
    def list_animals(self) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def list_milk(self) -> List[Dict[str, Any]]: ...
