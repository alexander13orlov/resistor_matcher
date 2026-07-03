# src/analysis/topology_optimizer.py
# Python 3.11+
# Оптимизированный поиск комбинаций резисторов по топологиям

from typing import Optional, List, Tuple, Callable, Dict, Any, Set
import logging
import bisect
import time
import heapq
import math
from collections import defaultdict
from functools import lru_cache

logger = logging.getLogger(__name__)


# =====================================================================
# Топологии для 4 резисторов
# =====================================================================

def topo_4_1(r: Tuple[float, ...]) -> float:
    """Четыре последовательно: R1 + R2 + R3 + R4"""
    return r[0] + r[1] + r[2] + r[3]

def topo_4_2(r: Tuple[float, ...]) -> float:
    """Четыре параллельно: 1/(1/R1 + 1/R2 + 1/R3 + 1/R4)"""
    return 1.0 / (1.0/r[0] + 1.0/r[1] + 1.0/r[2] + 1.0/r[3])

def topo_4_3(r: Tuple[float, ...]) -> float:
    """Три последовательно, параллельно четвёртому: (R1+R2+R3) || R4"""
    r123 = r[0] + r[1] + r[2]
    return (r123 * r[3]) / (r123 + r[3])

def topo_4_4(r: Tuple[float, ...]) -> float:
    """Три параллельно, последовательно с четвёртым: (R1||R2||R3) + R4"""
    r123 = 1.0 / (1.0/r[0] + 1.0/r[1] + 1.0/r[2])
    return r123 + r[3]

def topo_4_5(r: Tuple[float, ...]) -> float:
    """Две последовательные пары параллельно: (R1+R2) || (R3+R4)"""
    r12 = r[0] + r[1]
    r34 = r[2] + r[3]
    return (r12 * r34) / (r12 + r34)

def topo_4_6(r: Tuple[float, ...]) -> float:
    """Две параллельные пары последовательно: (R1||R2) + (R3||R4)"""
    r12 = (r[0] * r[1]) / (r[0] + r[1])
    r34 = (r[2] * r[3]) / (r[2] + r[3])
    return r12 + r34

def topo_4_7(r: Tuple[float, ...]) -> float:
    """Последовательно-параллельно-последовательно: R1 + (R2||R3) + R4"""
    r23 = (r[1] * r[2]) / (r[1] + r[2])
    return r[0] + r23 + r[3]

def topo_4_8(r: Tuple[float, ...]) -> float:
    """Параллельно-последовательно-параллельно: ((R1||R2) + R3) || R4"""
    r12 = (r[0] * r[1]) / (r[0] + r[1])
    r123 = r12 + r[2]
    return (r123 * r[3]) / (r123 + r[3])

def topo_4_9(r: Tuple[float, ...]) -> float:
    """Последовательный резистор и параллель двух ветвей: R1 + (R2 || (R3+R4))"""
    r34 = r[2] + r[3]
    r234 = (r[1] * r34) / (r[1] + r34)
    return r[0] + r234

def topo_4_10(r: Tuple[float, ...]) -> float:
    """Параллельный резистор и последовательная цепочка: R1 || (R2+R3+R4)"""
    r234 = r[1] + r[2] + r[3]
    return (r[0] * r234) / (r[0] + r234)

# =====================================================================
# Топологии для 3 резисторов
# =====================================================================

def topo_3_1(r: Tuple[float, ...]) -> float:
    """Три последовательно: R1 + R2 + R3"""
    return r[0] + r[1] + r[2]

def topo_3_2(r: Tuple[float, ...]) -> float:
    """Три параллельно: 1/(1/R1 + 1/R2 + 1/R3)"""
    return 1.0 / (1.0/r[0] + 1.0/r[1] + 1.0/r[2])

def topo_3_3(r: Tuple[float, ...]) -> float:
    """Два последовательно, параллельно третьему: (R1+R2) || R3"""
    r12 = r[0] + r[1]
    return (r12 * r[2]) / (r12 + r[2])

def topo_3_4(r: Tuple[float, ...]) -> float:
    """Два параллельно, последовательно с третьим: (R1||R2) + R3"""
    r12 = (r[0] * r[1]) / (r[0] + r[1])
    return r12 + r[2]

# =====================================================================
# Топологии для 2 резисторов
# =====================================================================

def topo_2_1(r: Tuple[float, ...]) -> float:
    """Два последовательно: R1 + R2"""
    return r[0] + r[1]

def topo_2_2(r: Tuple[float, ...]) -> float:
    """Два параллельно: (R1 * R2) / (R1 + R2)"""
    return (r[0] * r[1]) / (r[0] + r[1])

# =====================================================================
# Топология для 1 резистора
# =====================================================================

def topo_1_1(r: Tuple[float, ...]) -> float:
    """Один резистор: R1"""
    return r[0]

# =====================================================================
# Списки топологий
# =====================================================================

ALL_TOPOLOGIES: Dict[str, Callable[[Tuple[float, ...]], float]] = {
    "4-1": topo_4_1,
    "4-2": topo_4_2,
    "4-3": topo_4_3,
    "4-4": topo_4_4,
    "4-5": topo_4_5,
    "4-6": topo_4_6,
    "4-7": topo_4_7,
    "4-8": topo_4_8,
    "4-9": topo_4_9,
    "4-10": topo_4_10,
    "3-1": topo_3_1,
    "3-2": topo_3_2,
    "3-3": topo_3_3,
    "3-4": topo_3_4,
    "2-1": topo_2_1,
    "2-2": topo_2_2,
    "1-1": topo_1_1,
}

# Информация о структуре каждой топологии
TOPO_STRUCTURE: Dict[str, Dict[str, Any]] = {
    "4-1": {"type": "4", "structure": "2+2", "op": "sum", "formula": "R1+R2+R3+R4"},
    "4-2": {"type": "4", "structure": "2+2", "op": "parallel", "formula": "1/(1/R1+1/R2+1/R3+1/R4)"},
    "4-3": {"type": "4", "structure": "3+1", "op": "parallel", "formula": "(R1+R2+R3)||R4"},
    "4-4": {"type": "4", "structure": "3+1", "op": "sum", "formula": "(R1||R2||R3)+R4"},
    "4-5": {"type": "4", "structure": "2+2", "op": "parallel", "formula": "(R1+R2)||(R3+R4)"},
    "4-6": {"type": "4", "structure": "2+2", "op": "sum", "formula": "(R1||R2)+(R3||R4)"},
    "4-7": {"type": "4", "structure": "1+2+1", "op": "sum", "formula": "R1+(R2||R3)+R4"},
    "4-8": {"type": "4", "structure": "2+1+1", "op": "parallel", "formula": "((R1||R2)+R3)||R4"},
    "4-9": {"type": "4", "structure": "1+1+2", "op": "sum", "formula": "R1+(R2||(R3+R4))"},
    "4-10": {"type": "4", "structure": "1+3", "op": "parallel", "formula": "R1||(R2+R3+R4)"},
    "3-1": {"type": "3", "structure": "2+1", "op": "sum", "formula": "R1+R2+R3"},
    "3-2": {"type": "3", "structure": "2+1", "op": "parallel", "formula": "1/(1/R1+1/R2+1/R3)"},
    "3-3": {"type": "3", "structure": "2+1", "op": "parallel", "formula": "(R1+R2)||R3"},
    "3-4": {"type": "3", "structure": "2+1", "op": "sum", "formula": "(R1||R2)+R3"},
    "2-1": {"type": "2", "structure": "1+1", "op": "sum", "formula": "R1+R2"},
    "2-2": {"type": "2", "structure": "1+1", "op": "parallel", "formula": "R1||R2"},
    "1-1": {"type": "1", "structure": "1", "op": "single", "formula": "R1"},
}

# Группы топологий по структуре
STRUCTURE_GROUPS: Dict[str, List[str]] = {
    "2+2": ["4-1", "4-2", "4-5", "4-6"],
    "3+1": ["4-3", "4-4"],
    "1+2+1": ["4-7"],
    "2+1+1": ["4-8"],
    "1+1+2": ["4-9"],
    "1+3": ["4-10"],
    "2+1": ["3-1", "3-2", "3-3", "3-4"],
    "1+1": ["2-1", "2-2"],
    "1": ["1-1"],
}

# Быстрые структуры (O(n² log n) и меньше)
FAST_STRUCTURES = {"2+2", "2+1", "1+1", "1"}

# Сложные структуры (O(n³))
COMPLEX_STRUCTURES = {"3+1", "1+2+1", "2+1+1", "1+1+2", "1+3"}


class TopologySearcher:
    """
    Оптимизированный поиск размещений для заданных топологий.
    """
    
    def __init__(self, series: List[float], tolerances: Optional[List[float]] = None):
        """
        Args:
            series: Список номиналов (с повторениями)
            tolerances: Список точностей (соответствует series)
        """
        self.original_series = list(series)
        self.n = len(series)
        self.tolerances = tolerances if tolerances is not None else [0.0] * len(series)
        
        self.sorted_series = sorted(enumerate(series), key=lambda x: x[1])
        self.sorted_values = [v for _, v in self.sorted_series]
        self.sorted_indices = [i for i, _ in self.sorted_series]
        self.sorted_tolerances = [self.tolerances[i] for i, _ in self.sorted_series]
        
        self._pair_sums = None
        self._pair_parallel = None
        self._singles = None
        
        logger.info(f"TopologySearcher: n={self.n}")
    
    def _get_pair_sums(self) -> List[Tuple[float, int, int]]:
        if self._pair_sums is None:
            sums = []
            for i in range(self.n - 1):
                for j in range(i + 1, self.n):
                    s = self.sorted_values[i] + self.sorted_values[j]
                    sums.append((s, i, j))
            self._pair_sums = sums
        return self._pair_sums
    
    def _get_pair_parallel(self) -> List[Tuple[float, int, int]]:
        if self._pair_parallel is None:
            pairs = []
            for i in range(self.n - 1):
                for j in range(i + 1, self.n):
                    v = (self.sorted_values[i] * self.sorted_values[j]) / (self.sorted_values[i] + self.sorted_values[j])
                    pairs.append((v, i, j))
            self._pair_parallel = pairs
        return self._pair_parallel
    
    def _get_singles(self) -> List[Tuple[float, int]]:
        if self._singles is None:
            self._singles = [(self.sorted_values[i], i) for i in range(self.n)]
        return self._singles
    
    def _parallel(self, a: float, b: float) -> float:
        if a + b == 0:
            return 0.0
        return (a * b) / (a + b)
    
    def _get_tolerances(self, indices: Tuple[int, ...]) -> Tuple[float, ...]:
        """Получить точности для индексов."""
        return tuple(self.sorted_tolerances[i] for i in indices)
    
    def _calc_tolerance_for_indices(self, indices: Tuple[int, ...], topo_name: str) -> float:
        """Рассчитать точность сборки по формуле для заданных индексов."""
        values = tuple(self.sorted_values[i] for i in indices)
        tolerances = tuple(self.sorted_tolerances[i] for i in indices)
        return self._calc_tolerance_by_formula(values, tolerances, topo_name)
    
    def _calc_tolerance_by_formula(
        self, 
        values: Tuple[float, ...], 
        tolerances: Tuple[float, ...], 
        topo_name: str
    ) -> float:
        """Расчёт точности сборки по имени топологии."""
        if not tolerances or len(values) != len(tolerances):
            return 0.0
        
        size = len(values)
        if size == 1:
            return tolerances[0]
        
        # Получаем формулу из структуры
        formula = TOPO_STRUCTURE.get(topo_name, {}).get("formula", "")
        if not formula:
            return 0.0
        
        r1, r2, r3, r4 = values[0], values[1] if size > 1 else 0, values[2] if size > 2 else 0, values[3] if size > 3 else 0
        d1, d2, d3, d4 = tolerances[0], tolerances[1] if size > 1 else 0, tolerances[2] if size > 2 else 0, tolerances[3] if size > 3 else 0
        
        # =====================================================================
        # 2 резистора
        # =====================================================================
        if size == 2:
            if formula in ["R1+R2", "4-1", "3-1", "2-1"]:
                total = r1 + r2
                if total == 0:
                    return 0.0
                return math.sqrt((r1 * d1) ** 2 + (r2 * d2) ** 2) / total
            elif formula in ["R1||R2", "4-2", "4-5", "4-6", "3-2", "2-2"]:
                r_par = (r1 * r2) / (r1 + r2) if (r1 + r2) != 0 else 0
                if r_par == 0:
                    return 0.0
                return r_par * math.sqrt((d1 / r1) ** 2 + (d2 / r2) ** 2)
        
        # =====================================================================
        # 3 резистора
        # =====================================================================
        if size == 3:
            if formula in ["R1+R2+R3", "4-1", "3-1"]:
                total = r1 + r2 + r3
                if total == 0:
                    return 0.0
                return math.sqrt((r1 * d1) ** 2 + (r2 * d2) ** 2 + (r3 * d3) ** 2) / total
            elif formula in ["1/(1/R1+1/R2+1/R3)", "4-2", "3-2"]:
                inv_sum = 1.0 / r1 + 1.0 / r2 + 1.0 / r3
                r_par = 1.0 / inv_sum if inv_sum != 0 else 0
                if r_par == 0:
                    return 0.0
                return r_par * math.sqrt((d1 / r1) ** 2 + (d2 / r2) ** 2 + (d3 / r3) ** 2)
            elif formula in ["(R1+R2)||R3", "4-3", "4-5", "3-3"]:
                r12 = r1 + r2
                d12 = math.sqrt((r1 * d1) ** 2 + (r2 * d2) ** 2) / r12 if r12 != 0 else 0
                r_par = (r12 * r3) / (r12 + r3) if (r12 + r3) != 0 else 0
                if r_par == 0:
                    return 0.0
                return r_par * math.sqrt((d12 / r12) ** 2 + (d3 / r3) ** 2)
            elif formula in ["(R1||R2)+R3", "4-4", "4-6", "3-4"]:
                r12 = (r1 * r2) / (r1 + r2) if (r1 + r2) != 0 else 0
                d12 = r12 * math.sqrt((d1 / r1) ** 2 + (d2 / r2) ** 2) if r12 != 0 else 0
                total = r12 + r3
                if total == 0:
                    return 0.0
                return math.sqrt((r12 * d12) ** 2 + (r3 * d3) ** 2) / total
        
        # =====================================================================
        # 4 резистора
        # =====================================================================
        if size == 4:
            if formula in ["R1+R2+R3+R4", "4-1"]:
                total = r1 + r2 + r3 + r4
                if total == 0:
                    return 0.0
                return math.sqrt((r1 * d1) ** 2 + (r2 * d2) ** 2 + (r3 * d3) ** 2 + (r4 * d4) ** 2) / total
            
            elif formula in ["1/(1/R1+1/R2+1/R3+1/R4)", "4-2"]:
                inv_sum = 1.0 / r1 + 1.0 / r2 + 1.0 / r3 + 1.0 / r4
                r_par = 1.0 / inv_sum if inv_sum != 0 else 0
                if r_par == 0:
                    return 0.0
                return r_par * math.sqrt((d1 / r1) ** 2 + (d2 / r2) ** 2 + (d3 / r3) ** 2 + (d4 / r4) ** 2)
            
            elif formula in ["(R1+R2+R3)||R4", "4-3"]:
                r123 = r1 + r2 + r3
                d123 = math.sqrt((r1 * d1) ** 2 + (r2 * d2) ** 2 + (r3 * d3) ** 2) / r123 if r123 != 0 else 0
                r_par = (r123 * r4) / (r123 + r4) if (r123 + r4) != 0 else 0
                if r_par == 0:
                    return 0.0
                return r_par * math.sqrt((d123 / r123) ** 2 + (d4 / r4) ** 2)
            
            elif formula in ["(R1||R2||R3)+R4", "4-4"]:
                inv_sum = 1.0 / r1 + 1.0 / r2 + 1.0 / r3
                r123 = 1.0 / inv_sum if inv_sum != 0 else 0
                d123 = r123 * math.sqrt((d1 / r1) ** 2 + (d2 / r2) ** 2 + (d3 / r3) ** 2) if r123 != 0 else 0
                total = r123 + r4
                if total == 0:
                    return 0.0
                return math.sqrt((r123 * d123) ** 2 + (r4 * d4) ** 2) / total
            
            elif formula in ["(R1+R2)||(R3+R4)", "4-5"]:
                r12 = r1 + r2
                d12 = math.sqrt((r1 * d1) ** 2 + (r2 * d2) ** 2) / r12 if r12 != 0 else 0
                r34 = r3 + r4
                d34 = math.sqrt((r3 * d3) ** 2 + (r4 * d4) ** 2) / r34 if r34 != 0 else 0
                r_par = (r12 * r34) / (r12 + r34) if (r12 + r34) != 0 else 0
                if r_par == 0:
                    return 0.0
                return r_par * math.sqrt((d12 / r12) ** 2 + (d34 / r34) ** 2)
            
            elif formula in ["(R1||R2)+(R3||R4)", "4-6"]:
                r12 = (r1 * r2) / (r1 + r2) if (r1 + r2) != 0 else 0
                d12 = r12 * math.sqrt((d1 / r1) ** 2 + (d2 / r2) ** 2) if r12 != 0 else 0
                r34 = (r3 * r4) / (r3 + r4) if (r3 + r4) != 0 else 0
                d34 = r34 * math.sqrt((d3 / r3) ** 2 + (d4 / r4) ** 2) if r34 != 0 else 0
                total = r12 + r34
                if total == 0:
                    return 0.0
                return math.sqrt((r12 * d12) ** 2 + (r34 * d34) ** 2) / total
            
            elif formula in ["R1+(R2||R3)+R4", "4-7"]:
                r23 = (r2 * r3) / (r2 + r3) if (r2 + r3) != 0 else 0
                d23 = r23 * math.sqrt((d2 / r2) ** 2 + (d3 / r3) ** 2) if r23 != 0 else 0
                total = r1 + r23 + r4
                if total == 0:
                    return 0.0
                return math.sqrt((r1 * d1) ** 2 + (r23 * d23) ** 2 + (r4 * d4) ** 2) / total
            
            elif formula in ["((R1||R2)+R3)||R4", "4-8"]:
                r12 = (r1 * r2) / (r1 + r2) if (r1 + r2) != 0 else 0
                d12 = r12 * math.sqrt((d1 / r1) ** 2 + (d2 / r2) ** 2) if r12 != 0 else 0
                r123 = r12 + r3
                d123 = math.sqrt((r12 * d12) ** 2 + (r3 * d3) ** 2) / r123 if r123 != 0 else 0
                r_par = (r123 * r4) / (r123 + r4) if (r123 + r4) != 0 else 0
                if r_par == 0:
                    return 0.0
                return r_par * math.sqrt((d123 / r123) ** 2 + (d4 / r4) ** 2)
            
            elif formula in ["R1+(R2||(R3+R4))", "4-9"]:
                r34 = r3 + r4
                d34 = math.sqrt((r3 * d3) ** 2 + (r4 * d4) ** 2) / r34 if r34 != 0 else 0
                r234 = (r2 * r34) / (r2 + r34) if (r2 + r34) != 0 else 0
                d234 = r234 * math.sqrt((d2 / r2) ** 2 + (d34 / r34) ** 2) if r234 != 0 else 0
                total = r1 + r234
                if total == 0:
                    return 0.0
                return math.sqrt((r1 * d1) ** 2 + (r234 * d234) ** 2) / total
            
            elif formula in ["R1||(R2+R3+R4)", "4-10"]:
                r234 = r2 + r3 + r4
                d234 = math.sqrt((r2 * d2) ** 2 + (r3 * d3) ** 2 + (r4 * d4) ** 2) / r234 if r234 != 0 else 0
                r_par = (r1 * r234) / (r1 + r234) if (r1 + r234) != 0 else 0
                if r_par == 0:
                    return 0.0
                return r_par * math.sqrt((d1 / r1) ** 2 + (d234 / r234) ** 2)
        
        return 0.0
    
    def _find_best_2_2(
        self, 
        r_search: float, 
        pairs: List[Tuple[float, int, int]], 
        op: str,
        topo_name: str,
        n: int = 10
    ) -> List[Tuple[Tuple[int, ...], Tuple[float, ...], float, float, float]]:
        """
        Поиск для топологий вида: f(pair1, pair2)
        Возвращает: (индексы, значения, r_par, diff, точность_сборки)
        """
        if self.n < 4:
            return []
        
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        pair_vals = [p[0] for p in pairs_sorted]
        
        seen_combinations = set()
        best_results = []
        
        for a, i, j in pairs_sorted:
            if op == 'sum':
                target_b = r_search - a
                if target_b <= 0:
                    continue
            else:
                if a <= r_search:
                    continue
                target_b = (r_search * a) / (a - r_search)
                if target_b <= 0:
                    continue
            
            pos = bisect.bisect_left(pair_vals, target_b)
            search_range = min(20, len(pair_vals) // 10)
            
            for offset in range(-search_range, search_range + 1):
                p = pos + offset
                if 0 <= p < len(pair_vals):
                    b, k, l = pairs_sorted[p]
                    
                    indices_set = {i, j, k, l}
                    if len(indices_set) < 4:
                        continue
                    
                    if op == 'sum':
                        actual_r = a + b
                    else:
                        actual_r = self._parallel(a, b)
                    
                    diff = abs(actual_r - r_search)
                    
                    values_tuple = tuple(sorted([
                        self.sorted_values[i],
                        self.sorted_values[j],
                        self.sorted_values[k],
                        self.sorted_values[l]
                    ]))
                    if values_tuple in seen_combinations:
                        continue
                    seen_combinations.add(values_tuple)
                    
                    orig_indices = (
                        self.sorted_indices[i],
                        self.sorted_indices[j],
                        self.sorted_indices[k],
                        self.sorted_indices[l]
                    )
                    orig_values = (
                        self.sorted_values[i],
                        self.sorted_values[j],
                        self.sorted_values[k],
                        self.sorted_values[l]
                    )
                    
                    # Рассчитываем точность сборки
                    tol_total = self._calc_tolerance_for_indices(orig_indices, topo_name)
                    
                    if len(best_results) < n:
                        heapq.heappush(best_results, (-diff, orig_indices, orig_values, actual_r, tol_total))
                    else:
                        if diff < -best_results[0][0]:
                            heapq.heapreplace(best_results, (-diff, orig_indices, orig_values, actual_r, tol_total))
        
        results = []
        while best_results:
            neg_diff, indices, values, r_par, tol_total = heapq.heappop(best_results)
            results.append((indices, values, r_par, -neg_diff, tol_total))
        results.reverse()
        return results
    
    def _find_best_3_1(
        self, 
        r_search: float, 
        pairs: List[Tuple[float, int, int]], 
        op: str,
        topo_name: str,
        n: int = 10
    ) -> List[Tuple[Tuple[int, ...], Tuple[float, ...], float, float, float]]:
        """
        Поиск для топологий вида: f(pair, single)
        Возвращает: (индексы, значения, r_par, diff, точность_сборки)
        """
        if self.n < 3:
            return []
        
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        pair_vals = [p[0] for p in pairs_sorted]
        singles = self._get_singles()
        singles_sorted = sorted(singles, key=lambda x: x[0])
        single_vals = [s[0] for s in singles_sorted]
        
        seen_combinations = set()
        best_results = []
        
        for a, i, j in pairs_sorted:
            if op == 'sum':
                target_b = r_search - a
                if target_b <= 0:
                    continue
            else:
                if a <= r_search:
                    continue
                target_b = (r_search * a) / (a - r_search)
                if target_b <= 0:
                    continue
            
            pos = bisect.bisect_left(single_vals, target_b)
            search_range = min(10, len(single_vals) // 10)
            
            for offset in range(-search_range, search_range + 1):
                p = pos + offset
                if 0 <= p < len(single_vals):
                    b, k = singles_sorted[p]
                    
                    indices_set = {i, j, k}
                    if len(indices_set) < 3:
                        continue
                    
                    if op == 'sum':
                        actual_r = a + b
                    else:
                        actual_r = self._parallel(a, b)
                    
                    diff = abs(actual_r - r_search)
                    
                    values_tuple = tuple(sorted([
                        self.sorted_values[i],
                        self.sorted_values[j],
                        self.sorted_values[k]
                    ]))
                    if values_tuple in seen_combinations:
                        continue
                    seen_combinations.add(values_tuple)
                    
                    orig_indices = (
                        self.sorted_indices[i],
                        self.sorted_indices[j],
                        self.sorted_indices[k]
                    )
                    orig_values = (
                        self.sorted_values[i],
                        self.sorted_values[j],
                        self.sorted_values[k]
                    )
                    
                    tol_total = self._calc_tolerance_for_indices(orig_indices, topo_name)
                    
                    if len(best_results) < n:
                        heapq.heappush(best_results, (-diff, orig_indices, orig_values, actual_r, tol_total))
                    else:
                        if diff < -best_results[0][0]:
                            heapq.heapreplace(best_results, (-diff, orig_indices, orig_values, actual_r, tol_total))
        
        results = []
        while best_results:
            neg_diff, indices, values, r_par, tol_total = heapq.heappop(best_results)
            results.append((indices, values, r_par, -neg_diff, tol_total))
        results.reverse()
        return results
    
    def _find_best_1_1(
        self, 
        r_search: float, 
        op: str,
        topo_name: str,
        n: int = 10
    ) -> List[Tuple[Tuple[int, ...], Tuple[float, ...], float, float, float]]:
        """Поиск для топологий вида: f(single, single)."""
        if self.n < 2:
            return []
        
        singles = self._get_singles()
        singles_sorted = sorted(singles, key=lambda x: x[0])
        single_vals = [s[0] for s in singles_sorted]
        
        seen_combinations = set()
        best_results = []
        
        for a, i in singles_sorted:
            if op == 'sum':
                target_b = r_search - a
                if target_b <= 0:
                    continue
            else:
                if a <= r_search:
                    continue
                target_b = (r_search * a) / (a - r_search)
                if target_b <= 0:
                    continue
            
            pos = bisect.bisect_left(single_vals, target_b)
            search_range = min(10, len(single_vals) // 10)
            
            for offset in range(-search_range, search_range + 1):
                p = pos + offset
                if 0 <= p < len(single_vals):
                    b, j = singles_sorted[p]
                    
                    if i == j:
                        continue
                    
                    if op == 'sum':
                        actual_r = a + b
                    else:
                        actual_r = self._parallel(a, b)
                    
                    diff = abs(actual_r - r_search)
                    
                    values_tuple = tuple(sorted([a, b]))
                    if values_tuple in seen_combinations:
                        continue
                    seen_combinations.add(values_tuple)
                    
                    orig_indices = (self.sorted_indices[i], self.sorted_indices[j])
                    orig_values = (a, b)
                    
                    tol_total = self._calc_tolerance_for_indices(orig_indices, topo_name)
                    
                    if len(best_results) < n:
                        heapq.heappush(best_results, (-diff, orig_indices, orig_values, actual_r, tol_total))
                    else:
                        if diff < -best_results[0][0]:
                            heapq.heapreplace(best_results, (-diff, orig_indices, orig_values, actual_r, tol_total))
        
        results = []
        while best_results:
            neg_diff, indices, values, r_par, tol_total = heapq.heappop(best_results)
            results.append((indices, values, r_par, -neg_diff, tol_total))
        results.reverse()
        return results
    
    def _find_best_1(
        self, 
        r_search: float, 
        topo_name: str,
        n: int = 10
    ) -> List[Tuple[Tuple[int, ...], Tuple[float, ...], float, float, float]]:
        """Поиск ближайшего одиночного значения."""
        singles = self._get_singles()
        best_results = []
        
        for val, idx in singles:
            diff = abs(val - r_search)
            orig_indices = (self.sorted_indices[idx],)
            orig_values = (val,)
            tol_total = self._calc_tolerance_for_indices(orig_indices, topo_name)
            
            if len(best_results) < n:
                heapq.heappush(best_results, (-diff, orig_indices, orig_values, val, tol_total))
            else:
                if diff < -best_results[0][0]:
                    heapq.heapreplace(best_results, (-diff, orig_indices, orig_values, val, tol_total))
        
        results = []
        while best_results:
            neg_diff, indices, values, r_par, tol_total = heapq.heappop(best_results)
            results.append((indices, values, r_par, -neg_diff, tol_total))
        results.reverse()
        return results
    
    def _search_complex_topo(
        self, 
        target: float, 
        topo_name: str, 
        n: int = 10
    ) -> List[Tuple[Tuple[int, ...], Tuple[float, ...], float, float, float]]:
        """
        Прямой поиск для сложных топологий с эвристическим отбором.
        """
        topo_func = ALL_TOPOLOGIES[topo_name]
        
        max_val = target * 10
        min_val = target / 1000 if target > 0 else 0
        
        candidates = [(v, idx) for v, idx in zip(self.sorted_values, self.sorted_indices) 
                      if min_val <= v <= max_val]
        
        if len(candidates) < 4:
            return []
        
        if len(candidates) > 200:
            # Берём ближайшие к target
            candidates.sort(key=lambda x: abs(x[0] - target))
            candidates = candidates[:200]
        
        best_results = []
        seen_combinations = set()
        
        m = len(candidates)
        for i in range(m - 3):
            v1, idx1 = candidates[i]
            for j in range(i + 1, m - 2):
                v2, idx2 = candidates[j]
                for k in range(j + 1, m - 1):
                    v3, idx3 = candidates[k]
                    for l in range(k + 1, m):
                        v4, idx4 = candidates[l]
                        
                        values = (v1, v2, v3, v4)
                        indices = (idx1, idx2, idx3, idx4)
                        
                        values_tuple = tuple(sorted(values))
                        if values_tuple in seen_combinations:
                            continue
                        seen_combinations.add(values_tuple)
                        
                        try:
                            actual_r = topo_func(values)
                        except ZeroDivisionError:
                            continue
                        
                        diff = abs(actual_r - target)
                        
                        # Проверяем, что diff не слишком большой
                        if diff > target * 0.1:
                            continue
                        
                        tol_total = self._calc_tolerance_for_indices(indices, topo_name)
                        
                        if len(best_results) < n:
                            heapq.heappush(best_results, (-diff, indices, values, actual_r, tol_total))
                        else:
                            if diff < -best_results[0][0]:
                                heapq.heapreplace(best_results, (-diff, indices, values, actual_r, tol_total))
        
        results = []
        while best_results:
            neg_diff, indices, values, r_par, tol_total = heapq.heappop(best_results)
            results.append((indices, values, r_par, -neg_diff, tol_total))
        results.reverse()
        return results
    
    def search_topologies(
        self, 
        target: float, 
        topologies: List[str], 
        n: int = 10
    ) -> Dict[str, List[Tuple[Tuple[int, ...], Tuple[float, ...], float, float, float]]]:
        """
        Поиск для заданного списка топологий.
        
        Args:
            target: целевое значение r_par
            topologies: список имен топологий
            n: количество результатов на топологию
        
        Returns:
            Словарь {имя_топологии: [(индексы, значения, r_par, diff, точность_сборки), ...]}
        """
        results = {}
        
        for topo_name in topologies:
            if topo_name not in ALL_TOPOLOGIES:
                logger.warning(f"Неизвестная топология: {topo_name}")
                continue
            
            structure = TOPO_STRUCTURE[topo_name]
            topo_type = structure["type"]
            struct = structure["structure"]
            op = structure["op"]
            
            if topo_type == "4" and struct == "2+2":
                pairs = self._get_pair_sums() if op == "sum" else self._get_pair_parallel()
                results[topo_name] = self._find_best_2_2(target, pairs, op, topo_name, n)
            
            elif topo_type in ["4", "3"] and struct in ["3+1", "2+1"]:
                pairs = self._get_pair_sums() if op == "sum" else self._get_pair_parallel()
                results[topo_name] = self._find_best_3_1(target, pairs, op, topo_name, n)
            
            elif topo_type == "2" and struct == "1+1":
                results[topo_name] = self._find_best_1_1(target, op, topo_name, n)
            
            elif topo_type == "1" and struct == "1":
                results[topo_name] = self._find_best_1(target, topo_name, n)
            
            else:
                # Сложные топологии
                results[topo_name] = self._search_complex_topo(target, topo_name, n)
        
        return results
    
    def search_all_topologies(
        self, 
        target: float, 
        n: int = 10
    ) -> Dict[str, List[Tuple[Tuple[int, ...], Tuple[float, ...], float, float, float]]]:
        """Поиск для всех топологий."""
        return self.search_topologies(target, list(ALL_TOPOLOGIES.keys()), n)
    
    def search_fast_topologies(
        self, 
        target: float, 
        n: int = 10
    ) -> Dict[str, List[Tuple[Tuple[int, ...], Tuple[float, ...], float, float, float]]]:
        """Поиск только для быстрых топологий (2+2, 2+1, 1+1, 1)."""
        fast_topos = []
        for name in ALL_TOPOLOGIES.keys():
            structure = TOPO_STRUCTURE[name]["structure"]
            if structure in FAST_STRUCTURES:
                fast_topos.append(name)
        return self.search_topologies(target, fast_topos, n)