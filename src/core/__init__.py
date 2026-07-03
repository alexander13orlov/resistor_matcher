# src/core/__init__.py
# Python 3.11+
# Ядро: модели, загрузка, расчеты

from .loader import load_resistors_from_excel
from .models import Resistor
from .calculator import (
    calc_series,
    calc_parallel,
    calc_tolerance_series,
    calc_tolerance_parallel,
)

__all__ = [
    "load_resistors_from_excel",
    "Resistor",
    "calc_series",
    "calc_parallel",
    "calc_tolerance_series",
    "calc_tolerance_parallel",
]