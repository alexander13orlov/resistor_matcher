# src/analysis/selector.py
# Поиск комбинаций по диапазону или номиналу

from typing import List, Tuple, Dict, Optional


def search_by_range(
    detailed_results: List[Tuple[float, Tuple[float, ...], int, Tuple[float, ...], float]],
    r_min: float,
    r_max: float
) -> List[Tuple[float, Tuple[float, ...], int, Tuple[float, ...], float]]:
    """Поиск значений в диапазоне."""
    result = []
    for r_eq, v_tuple, topo_idx, tolerances, tol_total in detailed_results:
        if r_min <= r_eq <= r_max:
            result.append((r_eq, v_tuple, topo_idx, tolerances, tol_total))
    return result


def search_by_nominal(
    detailed_results: List[Tuple[float, Tuple[float, ...], int, Tuple[float, ...], float]],
    r_nominal: float,
    eps: int = 5
) -> List[Tuple[float, Tuple[float, ...], int, Tuple[float, ...], float]]:
    """Поиск ближайшего значения и окрестности."""
    if not detailed_results:
        return []

    closest_idx = 0
    min_diff = abs(detailed_results[0][0] - r_nominal)

    for i, (r_eq, _, _, _, _) in enumerate(detailed_results):
        diff = abs(r_eq - r_nominal)
        if diff < min_diff:
            min_diff = diff
            closest_idx = i

    start = max(0, closest_idx - eps)
    end = min(len(detailed_results) - 1, closest_idx + eps)

    result = []
    for i in range(start, end + 1):
        r_eq, v_tuple, topo_idx, tolerances, tol_total = detailed_results[i]
        result.append((r_eq, v_tuple, topo_idx, tolerances, tol_total))

    return result