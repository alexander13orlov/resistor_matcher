# src/analysis/optimized_combiner.py
# Python 3.11+
# Оптимизированный анализ комбинаций резисторов с использованием TopologySearcher

from typing import Sequence, Optional, List, Dict, Tuple, Any
import time
import logging
import heapq

from .topology_optimizer import TopologySearcher, ALL_TOPOLOGIES, TOPO_STRUCTURE, FAST_STRUCTURES

logger = logging.getLogger(__name__)


def get_topo_formula(topo_name: str) -> str:
    """Возвращает формулу для отображения по имени топологии."""
    formulas = {
        "4-1": "R1+R2+R3+R4",
        "4-2": "1/(1/R1+1/R2+1/R3+1/R4)",
        "4-3": "(R1+R2+R3)||R4",
        "4-4": "(R1||R2||R3)+R4",
        "4-5": "(R1+R2)||(R3+R4)",
        "4-6": "(R1||R2)+(R3||R4)",
        "4-7": "R1+(R2||R3)+R4",
        "4-8": "((R1||R2)+R3)||R4",
        "4-9": "R1+(R2||(R3+R4))",
        "4-10": "R1||(R2+R3+R4)",
        "3-1": "R1+R2+R3",
        "3-2": "1/(1/R1+1/R2+1/R3)",
        "3-3": "(R1+R2)||R3",
        "3-4": "(R1||R2)+R3",
        "2-1": "R1+R2",
        "2-2": "R1||R2",
        "1-1": "R1",
    }
    return formulas.get(topo_name, topo_name)


def _quick_single_search(
    available_resistors: Sequence[float],
    tolerances: Sequence[float],
    target: float,
    n_results: int = 10
) -> Dict[str, Any]:
    """
    Быстрый поиск одиночных резисторов (без создания TopologySearcher).
    Возвращает ВСЕ уникальные номиналы.
    """
    # Собираем уникальные номиналы с их точностями
    unique_map = {}
    for r, t in zip(available_resistors, tolerances):
        if r not in unique_map:
            unique_map[r] = t
    
    # Преобразуем в формат detailed_results (ВСЕ номиналы)
    detailed_results = []
    all_values = []
    
    topo_formulas = {0: "R1"}
    topo_names = {0: "1-1"}
    
    for r, t in unique_map.items():
        tolerances_tuple = (t,)
        detailed_results.append((r, (r,), 0, tolerances_tuple, t))
        all_values.append(r)
    
    all_values_sorted = sorted(all_values)
    detailed_results.sort(key=lambda x: x[0])
    
    return {
        'total_arrangements': len(all_values),
        'unique_value_tuples': len(set(all_values)),
        'topology_unique_counts': {"1-1": len(set(all_values))},
        'topology_unique_values': {},
        'topology_kept': {},
        'topology_discarded': {},
        'topology_names': topo_names,
        'topology_formulas': topo_formulas,
        'all_values': all_values,
        'all_values_sorted': all_values_sorted,
        'detailed_results': detailed_results,
        'total_values': len(all_values),
        'unique_count': len(set(all_values)),
        'logs': [f"Быстрый поиск одиночных резисторов завершён"],
        'timestamp_end': time.strftime('%Y-%m-%d %H:%M:%S'),
        'duration_seconds': 0.0,
        'optimized': True,
        'search_topologies': ["1-1"],
        'quick_single': True,
    }


def analyze_optimized(
    available_resistors: Sequence[float],
    tolerances: Optional[Sequence[float]] = None,
    target: float = 0.0,
    topologies: Optional[List[str]] = None,
    use_fast_only: bool = False,
    n_results: int = 10,
    include_all: bool = False,
) -> Dict[str, Any]:
    """
    Оптимизированный анализ комбинаций резисторов.
    
    Args:
        available_resistors: Список номиналов
        tolerances: Список точностей
        target: Целевое сопротивление для поиска
        topologies: Список топологий для поиска (если None — все)
        use_fast_only: Использовать только быстрые топологии
        n_results: Количество результатов на топологию
        include_all: Включить все найденные значения (не только лучшие)
    
    Returns:
        Словарь с результатами в формате, совместимом с combiner.py
    """
    start_time = time.time()
    
    if tolerances is None:
        tolerances = [0.0] * len(available_resistors)
    
    if len(available_resistors) != len(tolerances):
        raise ValueError("Длина списков номиналов и точностей должна совпадать")
    
    # Определяем топологии для поиска
    if topologies is not None:
        search_topos = topologies
    elif use_fast_only:
        search_topos = []
        for name in ALL_TOPOLOGIES.keys():
            structure = TOPO_STRUCTURE[name]["structure"]
            if structure in FAST_STRUCTURES:
                search_topos.append(name)
    else:
        search_topos = list(ALL_TOPOLOGIES.keys())
    
    # ================================================================
    # БЫСТРЫЙ ПУТЬ: только одиночные резисторы
    # ================================================================
    if search_topos == ["1-1"] or (len(search_topos) == 1 and search_topos[0] == "1-1"):
        return _quick_single_search(available_resistors, tolerances, target, n_results)
    
    # ================================================================
    # ОСНОВНОЙ ПУТЬ: создаём TopologySearcher
    # ================================================================
    
    # Создаём список с повторениями (каждый номинал 4 раза)
    expanded = []
    expanded_tol = []
    for r, t in zip(available_resistors, tolerances):
        for _ in range(4):
            expanded.append(r)
            expanded_tol.append(t)
    
    searcher = TopologySearcher(expanded, expanded_tol)
    
    # Выполняем поиск
    results = searcher.search_topologies(target, search_topos, n_results)
    
    # Преобразуем в формат, совместимый с combiner.py
    detailed_results = []
    all_values = []
    
    topo_names = {}
    topo_formulas = {}
    
    for idx, topo_name in enumerate(search_topos):
        topo_names[idx] = topo_name
        topo_formulas[idx] = get_topo_formula(topo_name)
        
        if topo_name in results and results[topo_name]:
            for indices, values, r_par, diff, tol_total in results[topo_name]:
                tolerances_tuple = tuple(searcher.sorted_tolerances[i] for i in indices)
                detailed_results.append((r_par, values, idx, tolerances_tuple, tol_total))
                all_values.append(r_par)
    
    all_values_sorted = sorted(all_values)
    detailed_results.sort(key=lambda x: x[0])
    
    return {
        'total_arrangements': len(all_values),
        'unique_value_tuples': len(set(all_values)),
        'topology_unique_counts': {topo_names.get(i, f"Схема {i}"): 0 for i in range(len(search_topos))},
        'topology_unique_values': {},
        'topology_kept': {},
        'topology_discarded': {},
        'topology_names': topo_names,
        'topology_formulas': topo_formulas,
        'all_values': all_values,
        'all_values_sorted': all_values_sorted,
        'detailed_results': detailed_results,
        'total_values': len(all_values),
        'unique_count': len(set(all_values)),
        'logs': [f"Оптимизированный анализ завершён за {time.time() - start_time:.3f} сек"],
        'timestamp_end': time.strftime('%Y-%m-%d %H:%M:%S'),
        'duration_seconds': time.time() - start_time,
        'optimized': True,
        'search_topologies': search_topos,
    }