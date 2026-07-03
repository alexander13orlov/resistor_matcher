# src/analysis/__init__.py
# Python 3.11+
# Анализ комбинаций резисторов

from .topologies import (
    TOPOLOGIES_1, TOPO_FORMULAS_1,
    TOPOLOGIES_2, TOPO_FORMULAS_2,
    TOPOLOGIES_3, TOPO_FORMULAS_3,
    TOPOLOGIES_4, TOPO_FORMULAS_4,
    get_topologies,
)
from .combiner import analyze_resistor_combinations
from .optimized_combiner import analyze_optimized
from .selector import search_by_range, search_by_nominal
from .topology_optimizer import (
    ALL_TOPOLOGIES,
    TOPO_STRUCTURE,
    STRUCTURE_GROUPS,
    FAST_STRUCTURES,
    COMPLEX_STRUCTURES,
    TopologySearcher,
)

__all__ = [
    "TOPOLOGIES_1", "TOPO_FORMULAS_1",
    "TOPOLOGIES_2", "TOPO_FORMULAS_2",
    "TOPOLOGIES_3", "TOPO_FORMULAS_3",
    "TOPOLOGIES_4", "TOPO_FORMULAS_4",
    "get_topologies",
    "analyze_resistor_combinations",
    "analyze_optimized",
    "search_by_range",
    "search_by_nominal",
    "ALL_TOPOLOGIES",
    "TOPO_STRUCTURE",
    "STRUCTURE_GROUPS",
    "FAST_STRUCTURES",
    "COMPLEX_STRUCTURES",
    "TopologySearcher",
]