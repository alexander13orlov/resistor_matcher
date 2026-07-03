# src/analysis/combiner.py
# Python 3.11+
# Основная логика анализа комбинаций резисторов с корректным расчётом точности

from itertools import permutations
from collections import defaultdict
from typing import Sequence, Optional, List, Dict, Tuple, Set, Callable
import time
import math

from .topologies import get_topologies, format_tuple
from ..core.calculator import calc_series, calc_parallel


def calc_tolerance_by_formula(
    values: Tuple[float, ...],
    tolerances: Tuple[float, ...],
    formula: str,
    size: int
) -> float:
    """
    Расчёт точности сборки по формуле топологии.
    
    Args:
        values: Кортеж номиналов резисторов
        tolerances: Кортеж точностей резисторов (в долях)
        formula: Строка с формулой топологии
        size: Количество резисторов
    
    Returns:
        float: Точность сборки (в долях)
    """
    if not tolerances or len(values) != len(tolerances):
        return 0.0
    
    # =====================================================================
    # 1 резистор
    # =====================================================================
    if size == 1:
        return tolerances[0]
    
    # =====================================================================
    # 2 резистора
    # =====================================================================
    if size == 2:
        r1, r2 = values[0], values[1]
        d1, d2 = tolerances[0], tolerances[1]
        
        if formula == "R1+R2":
            total = r1 + r2
            if total == 0:
                return 0.0
            return math.sqrt((r1 * d1) ** 2 + (r2 * d2) ** 2) / total
        
        elif formula == "R1||R2":
            r_par = (r1 * r2) / (r1 + r2) if (r1 + r2) != 0 else 0
            if r_par == 0:
                return 0.0
            return r_par * math.sqrt((d1 / r1) ** 2 + (d2 / r2) ** 2)
    
    # =====================================================================
    # 3 резистора
    # =====================================================================
    if size == 3:
        r1, r2, r3 = values[0], values[1], values[2]
        d1, d2, d3 = tolerances[0], tolerances[1], tolerances[2]
        
        if formula == "R1+R2+R3":
            total = r1 + r2 + r3
            if total == 0:
                return 0.0
            return math.sqrt(
                (r1 * d1) ** 2 + (r2 * d2) ** 2 + (r3 * d3) ** 2
            ) / total
        
        elif formula == "1/(1/R1+1/R2+1/R3)":
            inv_sum = 1.0 / r1 + 1.0 / r2 + 1.0 / r3
            r_par = 1.0 / inv_sum if inv_sum != 0 else 0
            if r_par == 0:
                return 0.0
            return r_par * math.sqrt(
                (d1 / r1) ** 2 + (d2 / r2) ** 2 + (d3 / r3) ** 2
            )
        
        elif formula == "(R1+R2)||R3":
            r12 = r1 + r2
            d12 = math.sqrt((r1 * d1) ** 2 + (r2 * d2) ** 2) / r12 if r12 != 0 else 0
            r_par = (r12 * r3) / (r12 + r3) if (r12 + r3) != 0 else 0
            if r_par == 0:
                return 0.0
            return r_par * math.sqrt((d12 / r12) ** 2 + (d3 / r3) ** 2)
        
        elif formula == "(R1||R2)+R3":
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
        r1, r2, r3, r4 = values[0], values[1], values[2], values[3]
        d1, d2, d3, d4 = tolerances[0], tolerances[1], tolerances[2], tolerances[3]
        
        if formula == "R1+R2+R3+R4":
            total = r1 + r2 + r3 + r4
            if total == 0:
                return 0.0
            return math.sqrt(
                (r1 * d1) ** 2 + (r2 * d2) ** 2 + (r3 * d3) ** 2 + (r4 * d4) ** 2
            ) / total
        
        elif formula == "1/(1/R1+1/R2+1/R3+1/R4)":
            inv_sum = 1.0 / r1 + 1.0 / r2 + 1.0 / r3 + 1.0 / r4
            r_par = 1.0 / inv_sum if inv_sum != 0 else 0
            if r_par == 0:
                return 0.0
            return r_par * math.sqrt(
                (d1 / r1) ** 2 + (d2 / r2) ** 2 + (d3 / r3) ** 2 + (d4 / r4) ** 2
            )
        
        elif formula == "(R1+R2+R3)||R4":
            r123 = r1 + r2 + r3
            d123 = math.sqrt(
                (r1 * d1) ** 2 + (r2 * d2) ** 2 + (r3 * d3) ** 2
            ) / r123 if r123 != 0 else 0
            r_par = (r123 * r4) / (r123 + r4) if (r123 + r4) != 0 else 0
            if r_par == 0:
                return 0.0
            return r_par * math.sqrt((d123 / r123) ** 2 + (d4 / r4) ** 2)
        
        elif formula == "(R1||R2||R3)+R4":
            inv_sum = 1.0 / r1 + 1.0 / r2 + 1.0 / r3
            r123 = 1.0 / inv_sum if inv_sum != 0 else 0
            d123 = r123 * math.sqrt(
                (d1 / r1) ** 2 + (d2 / r2) ** 2 + (d3 / r3) ** 2
            ) if r123 != 0 else 0
            total = r123 + r4
            if total == 0:
                return 0.0
            return math.sqrt((r123 * d123) ** 2 + (r4 * d4) ** 2) / total
        
        elif formula == "(R1+R2)||(R3+R4)":
            r12 = r1 + r2
            d12 = math.sqrt((r1 * d1) ** 2 + (r2 * d2) ** 2) / r12 if r12 != 0 else 0
            r34 = r3 + r4
            d34 = math.sqrt((r3 * d3) ** 2 + (r4 * d4) ** 2) / r34 if r34 != 0 else 0
            r_par = (r12 * r34) / (r12 + r34) if (r12 + r34) != 0 else 0
            if r_par == 0:
                return 0.0
            return r_par * math.sqrt((d12 / r12) ** 2 + (d34 / r34) ** 2)
        
        elif formula == "(R1||R2)+(R3||R4)":
            r12 = (r1 * r2) / (r1 + r2) if (r1 + r2) != 0 else 0
            d12 = r12 * math.sqrt((d1 / r1) ** 2 + (d2 / r2) ** 2) if r12 != 0 else 0
            r34 = (r3 * r4) / (r3 + r4) if (r3 + r4) != 0 else 0
            d34 = r34 * math.sqrt((d3 / r3) ** 2 + (d4 / r4) ** 2) if r34 != 0 else 0
            total = r12 + r34
            if total == 0:
                return 0.0
            return math.sqrt((r12 * d12) ** 2 + (r34 * d34) ** 2) / total
        
        elif formula == "R1+(R2||R3)+R4":
            r23 = (r2 * r3) / (r2 + r3) if (r2 + r3) != 0 else 0
            d23 = r23 * math.sqrt((d2 / r2) ** 2 + (d3 / r3) ** 2) if r23 != 0 else 0
            total = r1 + r23 + r4
            if total == 0:
                return 0.0
            return math.sqrt(
                (r1 * d1) ** 2 + (r23 * d23) ** 2 + (r4 * d4) ** 2
            ) / total
        
        elif formula == "((R1||R2)+R3)||R4":
            r12 = (r1 * r2) / (r1 + r2) if (r1 + r2) != 0 else 0
            d12 = r12 * math.sqrt((d1 / r1) ** 2 + (d2 / r2) ** 2) if r12 != 0 else 0
            r123 = r12 + r3
            d123 = math.sqrt((r12 * d12) ** 2 + (r3 * d3) ** 2) / r123 if r123 != 0 else 0
            r_par = (r123 * r4) / (r123 + r4) if (r123 + r4) != 0 else 0
            if r_par == 0:
                return 0.0
            return r_par * math.sqrt((d123 / r123) ** 2 + (d4 / r4) ** 2)
        
        elif formula == "R1+(R2||(R3+R4))":
            r34 = r3 + r4
            d34 = math.sqrt((r3 * d3) ** 2 + (r4 * d4) ** 2) / r34 if r34 != 0 else 0
            r234 = (r2 * r34) / (r2 + r34) if (r2 + r34) != 0 else 0
            d234 = r234 * math.sqrt((d2 / r2) ** 2 + (d34 / r34) ** 2) if r234 != 0 else 0
            total = r1 + r234
            if total == 0:
                return 0.0
            return math.sqrt((r1 * d1) ** 2 + (r234 * d234) ** 2) / total
        
        elif formula == "R1||(R2+R3+R4)":
            r234 = r2 + r3 + r4
            d234 = math.sqrt(
                (r2 * d2) ** 2 + (r3 * d3) ** 2 + (r4 * d4) ** 2
            ) / r234 if r234 != 0 else 0
            r_par = (r1 * r234) / (r1 + r234) if (r1 + r234) != 0 else 0
            if r_par == 0:
                return 0.0
            return r_par * math.sqrt((d1 / r1) ** 2 + (d234 / r234) ** 2)
    
    return 0.0


def analyze_resistor_combinations(
    available_resistors: Sequence[float],
    tolerances: Optional[Sequence[float]] = None,
    round_precision: Optional[int] = 3,
    include_4: bool = True,
    include_3: bool = False,
    include_2: bool = False,
    include_1: bool = False,
    verbose_tuples: bool = False,
    verbose_details: bool = False,
    verbose_details_limit: int = 100
) -> Dict:
    """
    Анализ всех возможных размещений резисторов с учётом порядка.
    """
    timestamp_start = time.time()
    log_entries: List[str] = []

    if tolerances is None:
        tolerances = [0.0] * len(available_resistors)

    if len(available_resistors) != len(tolerances):
        raise ValueError("Длина списков номиналов и точностей должна совпадать")

    all_topologies = get_topologies(include_1, include_2, include_3, include_4)

    if not all_topologies:
        log_entries.append("Ошибка: не выбрано ни одной схемы")
        return {
            'total_arrangements': 0,
            'unique_value_tuples': 0,
            'topology_unique_counts': {},
            'topology_unique_values': {},
            'topology_kept': {},
            'topology_discarded': {},
            'topology_names': {},
            'topology_formulas': {},
            'all_values': [],
            'all_values_sorted': [],
            'detailed_results': [],
            'total_values': 0,
            'unique_count': 0,
            'logs': log_entries,
            'timestamp_end': time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_seconds': 0.0
        }

    total_topologies = len(all_topologies)

    log_entries.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Начало анализа")
    log_entries.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Всего резисторов: {len(available_resistors)}")
    log_entries.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Уникальных номиналов: {len(set(available_resistors))}")
    log_entries.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Всего топологий: {total_topologies}")

    # Сбор уникальных кортежей для каждого размера
    tuples_by_size: Dict[int, Set[Tuple[float, ...]]] = {}
    total_arrangements = 0

    n = len(available_resistors)
    indices = list(range(n))

    sizes_needed: Set[int] = set()
    if include_1:
        sizes_needed.add(1)
    if include_2:
        sizes_needed.add(2)
    if include_3:
        sizes_needed.add(3)
    if include_4:
        sizes_needed.add(4)

    for size in sorted(sizes_needed):
        if n < size:
            log_entries.append(f"  Пропуск размера {size}: недостаточно резисторов")
            continue

        all_arrangements = list(permutations(indices, size))
        total_arrangements += len(all_arrangements)

        tuples_set: Set[Tuple[float, ...]] = set()
        for arr_indices in all_arrangements:
            value_tuple = tuple(available_resistors[i] for i in arr_indices)
            tuples_set.add(value_tuple)

        tuples_by_size[size] = tuples_set
        log_entries.append(
            f"  Размещений A({n},{size}): {len(all_arrangements)}, "
            f"уникальных кортежей: {len(tuples_set)}"
        )

    total_unique_tuples = sum(len(v) for v in tuples_by_size.values())
    log_entries.append(f"  Всего размещений: {total_arrangements}")
    log_entries.append(f"  Всего уникальных кортежей: {total_unique_tuples}")

    # Инициализация структур
    topology_unique_sets: Dict[int, Set[float]] = {}
    topology_discarded: Dict[int, int] = {}
    topology_kept: Dict[int, int] = {}
    topology_names: Dict[int, str] = {}
    topology_formulas: Dict[int, str] = {}

    all_values: List[float] = []
    detailed_results: List[Tuple[float, Tuple[float, ...], int, Tuple[float, ...], float]] = []

    for topo_idx, (topo_func, formula, size) in enumerate(all_topologies):
        topology_unique_sets[topo_idx] = set()
        topology_discarded[topo_idx] = 0
        topology_kept[topo_idx] = 0
        topology_names[topo_idx] = f"Схема {topo_idx+1} ({size} рез.)"
        topology_formulas[topo_idx] = formula

        if size not in tuples_by_size:
            continue

        groups_by_r: Dict[float, List[Tuple[float, ...]]] = defaultdict(list)

        for value_tuple in tuples_by_size[size]:
            try:
                r_eq = topo_func(value_tuple)
                if round_precision is not None:
                    r_eq = round(r_eq, round_precision)
                groups_by_r[r_eq].append(value_tuple)
            except ZeroDivisionError:
                pass

        for r_eq, tuple_list in groups_by_r.items():
            seen_sets: Set[frozenset] = set()
            kept_tuples: List[Tuple[float, ...]] = []

            for t in tuple_list:
                t_set = frozenset(t)
                if t_set not in seen_sets:
                    seen_sets.add(t_set)
                    kept_tuples.append(t)
                else:
                    topology_discarded[topo_idx] += 1

            topology_unique_sets[topo_idx].add(r_eq)

            for t in kept_tuples:
                topology_kept[topo_idx] += 1
                all_values.append(r_eq)

                # Собираем точности для этого кортежа
                tol_list = []
                for val in t:
                    for i, r_val in enumerate(available_resistors):
                        if r_val == val:
                            tol_list.append(tolerances[i])
                            break
                tolerances_tuple = tuple(tol_list)

                # Расчёт точности сборки по формуле
                tol_total = calc_tolerance_by_formula(
                    t, tolerances_tuple, formula, size
                )

                detailed_results.append((r_eq, t, topo_idx, tolerances_tuple, tol_total))

    all_values_sorted = sorted(all_values)
    detailed_results.sort(key=lambda x: x[0])

    # Статистика
    topology_unique_counts: Dict[str, int] = {}
    for i in range(total_topologies):
        name = topology_names.get(i, f"Схема {i+1}")
        topology_unique_counts[name] = len(topology_unique_sets.get(i, set()))

    topology_unique_values: Dict[str, List[float]] = {}
    for i in range(total_topologies):
        name = topology_names.get(i, f"Схема {i+1}")
        topology_unique_values[name] = sorted(topology_unique_sets.get(i, set()))

    results = {
        'total_arrangements': total_arrangements,
        'unique_value_tuples': total_unique_tuples,
        'topology_unique_counts': topology_unique_counts,
        'topology_unique_values': topology_unique_values,
        'topology_kept': topology_kept,
        'topology_discarded': topology_discarded,
        'topology_names': topology_names,
        'topology_formulas': topology_formulas,
        'all_values': all_values,
        'all_values_sorted': all_values_sorted,
        'detailed_results': detailed_results,
        'total_values': len(all_values),
        'unique_count': len(set(all_values)),
        'logs': log_entries,
        'timestamp_end': time.strftime('%Y-%m-%d %H:%M:%S'),
        'duration_seconds': round(time.time() - timestamp_start, 3)
    }

    log_entries.append(f"[{results['timestamp_end']}] Анализ завершён за {results['duration_seconds']} сек")
    return results