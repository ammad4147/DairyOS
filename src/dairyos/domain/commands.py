# src/dairyos/domain/commands.py
"""Simple command dataclass."""
from dataclasses import dataclass
from typing import Any


@dataclass
class Command:
    name: str
    payload: dict[str, Any]
