# src/dairyos/domain/commands.py
"""Simple command dataclass."""
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Command:
    name: str
    payload: Dict[str, Any]
