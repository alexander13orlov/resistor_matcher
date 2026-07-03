# src/core/models.py
# Python 3.11+
# Модели данных

from dataclasses import dataclass
from typing import Optional


@dataclass
class Resistor:
    """Модель резистора из базы."""
    nominal: float
    tolerance: float
    stock: int
    name: str
    type_name: str

    def __repr__(self) -> str:
        return f"{self.name} ({self.nominal}Ω ±{self.tolerance:.3f})"