# src/__init__.py
# Python 3.11+
# Основной пакет resistor_matcher

from .core.loader import load_resistors_from_excel
from .core.models import Resistor
from .core.calculator import calc_series, calc_parallel, calc_tolerance_series, calc_tolerance_parallel
from .analysis.combiner import analyze_resistor_combinations
from .analysis.selector import search_by_range, search_by_nominal
from .viz.density import plot_density, compute_local_density

__version__ = "0.1.0"
__all__ = [
    "load_resistors_from_excel",
    "Resistor",
    "calc_series",
    "calc_parallel",
    "calc_tolerance_series",
    "calc_tolerance_parallel",
    "analyze_resistor_combinations",
    "search_by_range",
    "search_by_nominal",
    "plot_density",
    "compute_local_density",
]