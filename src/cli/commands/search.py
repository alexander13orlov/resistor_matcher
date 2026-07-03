# src/cli/commands/search.py
# Поиск по номиналу или диапазону

import time
from typing import Optional, Dict, Union, List, Tuple
from pathlib import Path

from ...core.loader import load_resistors_from_excel
from ...analysis.combiner import analyze_resistor_combinations
from ...analysis.optimized_combiner import analyze_optimized
from ...analysis.selector import search_by_range, search_by_nominal
from ...analysis.topology_optimizer import ALL_TOPOLOGIES, FAST_STRUCTURES, STRUCTURE_GROUPS, TOPO_STRUCTURE
from ..utils import parse_range_nominals, filter_resistors_by_nominals
from ..output import print_search_results


def parse_topologies(topologies_str: str) -> List[str]:
    if not topologies_str:
        return []
    return [t.strip() for t in topologies_str.split(',') if t.strip() in ALL_TOPOLOGIES]


def parse_structure(structure_str: str) -> List[str]:
    if not structure_str:
        return []
    structures = [s.strip() for s in structure_str.split(',')]
    topologies = []
    for s in structures:
        if s in STRUCTURE_GROUPS:
            topologies.extend(STRUCTURE_GROUPS[s])
    return topologies


def get_topologies_by_flags(inc4: bool, inc3: bool, inc2: bool, inc1: bool) -> List[str]:
    topologies = []
    if inc4:
        topologies.extend(["4-1", "4-2", "4-3", "4-4", "4-5", "4-6", "4-7", "4-8", "4-9", "4-10"])
    if inc3:
        topologies.extend(["3-1", "3-2", "3-3", "3-4"])
    if inc2:
        topologies.extend(["2-1", "2-2"])
    if inc1:
        topologies.extend(["1-1"])
    return topologies


def split_topologies_by_speed(topologies: List[str]) -> Tuple[List[str], List[str]]:
    fast = []
    complex = []
    for topo in topologies:
        if topo in ALL_TOPOLOGIES:
            struct = TOPO_STRUCTURE[topo]["structure"]
            if struct in FAST_STRUCTURES:
                fast.append(topo)
            else:
                complex.append(topo)
    return fast, complex


def run_search(
    filepath: Union[str, Path],
    mode: str = "nominal",
    nominal: Optional[float] = None,
    r_min: Optional[float] = None,
    r_max: Optional[float] = None,
    eps: int = 10,
    range_nominals: str = "15",
    precision: int = 6,
    max_repeats: int = 4,
    inc4: bool = True,
    inc3: bool = True,
    inc2: bool = True,
    inc1: bool = True,
    show_details: bool = False,
    details_limit: int = 100,
    with_graph: bool = False,
    save_graph: Optional[str] = None,
    show_graph: bool = True,
    optimized: bool = True,
    topologies: Optional[str] = None,
    structure: Optional[str] = None,
    fast_only: bool = False,
    n_results: int = 10,
    auto_range: bool = False,
) -> Dict:
    """
    Поиск комбинаций резисторов.
    
    Returns:
        Dict: Словарь с результатами (включает 'search_results' и 'results')
    """
    start_time = time.time()
    timestamp_start = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp_start}] ========== ПОИСК КОМБИНАЦИЙ РЕЗИСТОРОВ ==========")

    try:
        resistors = load_resistors_from_excel(
            filepath, max_repeats_per_nominal=max_repeats
        )
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка загрузки: {e}")
        return {"error": str(e)}

    if not resistors:
        print("Ошибка: нет резисторов для анализа")
        return {"error": "no_resistors"}

    full_list = [r.nominal for r in resistors]
    tolerances_full = [r.tolerance for r in resistors]
    original_count = len(full_list)
    unique_original = sorted(set(full_list))

    if mode == "nominal":
        target = nominal
    else:
        target = (r_min + r_max) / 2 if r_min is not None and r_max is not None else None

    # ================================================================
    # ФОРМИРУЕМ СПИСОК ТОПОЛОГИЙ
    # ================================================================
    if topologies:
        search_topologies = parse_topologies(topologies)
    elif structure:
        search_topologies = parse_structure(structure)
    elif fast_only:
        search_topologies = []
        for name in ALL_TOPOLOGIES.keys():
            struct = TOPO_STRUCTURE[name]["structure"]
            if struct in FAST_STRUCTURES:
                search_topologies.append(name)
    else:
        search_topologies = get_topologies_by_flags(inc4, inc3, inc2, inc1)

    # ================================================================
    # РАЗДЕЛЯЕМ НА БЫСТРЫЕ И СЛОЖНЫЕ
    # ================================================================
    fast_topos, complex_topos = split_topologies_by_speed(search_topologies)

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Топологии:")
    print(f"  Быстрые: {', '.join(fast_topos) if fast_topos else 'нет'}")
    print(f"  Сложные: {', '.join(complex_topos) if complex_topos else 'нет'}")

    # ================================================================
    # ПРОВЕРКА target
    # ================================================================
    if target is None:
        print("Ошибка: не указано целевое сопротивление")
        return {"error": "missing_target"}

    # ================================================================
    # ПОИСК ДЛЯ БЫСТРЫХ ТОПОЛОГИЙ
    # ================================================================
    all_detailed = []
    all_topo_formulas = {}
    all_topo_names = {}
    all_results = {}

    if fast_topos:
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Поиск по быстрым топологиям...")

        use_filter = not (auto_range and optimized)

        if use_filter and range_nominals != "0":
            left, right = parse_range_nominals(range_nominals)
            filtered = filter_resistors_by_nominals(full_list, target, left, right)
            filtered_set = set(filtered)
            resistor_list = sorted(filtered_set)
            tolerances_list = []
            for val in resistor_list:
                for i, r_val in enumerate(full_list):
                    if r_val == val:
                        tolerances_list.append(tolerances_full[i])
                        break
            print(f"  Фильтрация: {len(resistor_list)} уникальных номиналов")
        else:
            resistor_list = unique_original
            tolerances_list = []
            for val in resistor_list:
                for i, r_val in enumerate(full_list):
                    if r_val == val:
                        tolerances_list.append(tolerances_full[i])
                        break
            print(f"  Без фильтрации: {len(resistor_list)} уникальных номиналов")

        results_fast = analyze_optimized(
            available_resistors=resistor_list,
            tolerances=tolerances_list,
            target=target,
            topologies=fast_topos,
            use_fast_only=False,
            n_results=n_results,
        )

        for idx, topo_name in enumerate(fast_topos):
            all_topo_names[len(all_topo_names)] = topo_name
            all_topo_formulas[len(all_topo_formulas)] = results_fast["topology_formulas"].get(idx, topo_name)

        base_idx = len(all_topo_names) - len(fast_topos)
        for r_eq, values, topo_idx, tolerances, tol_total in results_fast["detailed_results"]:
            new_idx = base_idx + topo_idx
            all_detailed.append((r_eq, values, new_idx, tolerances, tol_total))

        all_results["fast"] = results_fast
        print(f"  Найдено {len(results_fast['detailed_results'])} значений")

    # ================================================================
    # ПОИСК ДЛЯ СЛОЖНЫХ ТОПОЛОГИЙ
    # ================================================================
    if complex_topos:
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Поиск по сложным топологиям...")

        use_filter = True
        if range_nominals == "0":
            use_filter = False

        if use_filter:
            left, right = parse_range_nominals(range_nominals)
            filtered = filter_resistors_by_nominals(full_list, target, left, right)
            filtered_set = set(filtered)
            resistor_list = sorted(filtered_set)
            tolerances_list = []
            for val in resistor_list:
                for i, r_val in enumerate(full_list):
                    if r_val == val:
                        tolerances_list.append(tolerances_full[i])
                        break
            print(f"  Фильтрация: {len(resistor_list)} уникальных номиналов")
        else:
            resistor_list = unique_original
            tolerances_list = []
            for val in resistor_list:
                for i, r_val in enumerate(full_list):
                    if r_val == val:
                        tolerances_list.append(tolerances_full[i])
                        break
            print(f"  Без фильтрации: {len(resistor_list)} уникальных номиналов")

        results_complex = analyze_optimized(
            available_resistors=resistor_list,
            tolerances=tolerances_list,
            target=target,
            topologies=complex_topos,
            use_fast_only=False,
            n_results=n_results,
        )

        base_idx = len(all_topo_names)
        for idx, topo_name in enumerate(complex_topos):
            all_topo_names[base_idx + idx] = topo_name
            all_topo_formulas[base_idx + idx] = results_complex["topology_formulas"].get(idx, topo_name)

        for r_eq, values, topo_idx, tolerances, tol_total in results_complex["detailed_results"]:
            new_idx = base_idx + topo_idx
            all_detailed.append((r_eq, values, new_idx, tolerances, tol_total))

        all_results["complex"] = results_complex
        print(f"  Найдено {len(results_complex['detailed_results'])} значений")

    # ================================================================
    # ОБЪЕДИНЯЕМ РЕЗУЛЬТАТЫ
    # ================================================================
    all_detailed.sort(key=lambda x: x[0])
    all_values = [r for r, _, _, _, _ in all_detailed]

    total_values = len(all_values)
    unique_count = len(set(all_values))

    combined_results = {
        'total_arrangements': total_values,
        'unique_value_tuples': unique_count,
        'topology_unique_counts': {all_topo_names.get(i, f"Схема {i}"): 0 for i in range(len(all_topo_names))},
        'topology_unique_values': {},
        'topology_kept': {},
        'topology_discarded': {},
        'topology_names': all_topo_names,
        'topology_formulas': all_topo_formulas,
        'all_values': all_values,
        'all_values_sorted': sorted(all_values),
        'detailed_results': all_detailed,
        'total_values': total_values,
        'unique_count': unique_count,
        'logs': [],
        'timestamp_end': time.strftime('%Y-%m-%d %H:%M:%S'),
        'duration_seconds': time.time() - start_time,
        'optimized': True,
        'search_topologies': search_topologies,
    }

    detailed = all_detailed
    topo_formulas = all_topo_formulas
    results = combined_results

    analysis_time = time.time() - start_time

    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Анализ завершён:")
    print(f"  Всего значений в ряду: {total_values}")
    print(f"  Уникальных значений: {unique_count}")
    print(f"  Время анализа: {analysis_time:.2f} сек")

    if detailed:
        print(f"  Диапазон: [{detailed[0][0]:.6g} ... {detailed[-1][0]:.6g}] Ом")

    # ================================================================
    # ДЕТАЛИЗАЦИЯ
    # ================================================================
    if show_details:
        limit = min(details_limit, len(detailed))
        print(f"\n  Полная детализация (первые {limit} из {len(detailed)}):")
        print(f"  {'-' * 70}")
        from ...analysis.topologies import format_tuple
        for i in range(limit):
            r_eq, v_tuple, topo_idx, tolerances, tol_total = detailed[i]
            formula = topo_formulas.get(topo_idx, f"Схема {topo_idx + 1}")
            tol_str = f"{tol_total*100:.2f}%" if tol_total > 0 else "—"
            print(
                f"  [{i + 1}] R={r_eq:.6g} Ом | {formula} | {format_tuple(v_tuple)} | точность сб.: {tol_str}"
            )

    # ================================================================
    # ПОИСК (10 СЛЕВА + 10 СПРАВА ОТ БЛИЖАЙШЕГО)
    # ================================================================
    search_results = []

    if mode == "range":
        if r_min is None or r_max is None:
            print("Ошибка: не указаны границы диапазона")
            return {"error": "missing_bounds"}

        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Поиск в диапазоне [{r_min:.6g} ... {r_max:.6g}] Ом:")
        search_results = search_by_range(detailed, r_min, r_max)
        print_search_results(search_results, topo_formulas, target=(r_min + r_max) / 2)

    else:  # nominal
        if nominal is None:
            print("Ошибка: не указан номинал")
            return {"error": "missing_nominal"}

        if optimized and not results.get('quick_single', False):
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Поиск по номиналу {nominal:.6g} Ом (10 слева + 10 справа):")
            
            # 1. Сортируем по возрастанию R_экв
            detailed_sorted = sorted(detailed, key=lambda x: x[0])
            
            # 2. Находим все значения, равные closest_R
            closest_idx = min(range(len(detailed_sorted)), key=lambda i: abs(detailed_sorted[i][0] - nominal))
            closest_R = detailed_sorted[closest_idx][0]
            
            # 3. Находим первый и последний индекс с closest_R
            first_idx = closest_idx
            while first_idx > 0 and abs(detailed_sorted[first_idx - 1][0] - closest_R) < 1e-9:
                first_idx -= 1
            
            last_idx = closest_idx
            while last_idx < len(detailed_sorted) - 1 and abs(detailed_sorted[last_idx + 1][0] - closest_R) < 1e-9:
                last_idx += 1
            
            # 4. Берём 10 слева от первого closest_R и 10 справа от последнего
            start = max(0, first_idx - 10)
            end = min(len(detailed_sorted), last_idx + 11)
            
            search_results = detailed_sorted[start:end]
            
            # 5. Подсвечиваем все значения с closest_R
            highlight_indices = []
            for i, item in enumerate(search_results):
                if abs(item[0] - closest_R) < 1e-9:
                    highlight_indices.append(i)
            
            print_search_results(search_results, topo_formulas, target=nominal, highlight_idx=highlight_indices)
        else:
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Поиск по номиналу {nominal:.6g} Ом ±{eps} позиций:")
            search_results = search_by_nominal(detailed, nominal, eps)
            highlight_idx = None
            if search_results:
                closest_idx = min(range(len(search_results)), key=lambda i: abs(search_results[i][0] - nominal))
                highlight_idx = closest_idx
            print_search_results(search_results, topo_formulas, target=nominal, highlight_idx=highlight_idx)

    # ================================================================
    # ГРАФИК
    # ================================================================
    if with_graph and total_values > 0:
        from ...viz.density import plot_density
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Построение графика плотности...")
        plot_density(
            results["all_values_sorted"],
            source_nominals=resistor_list,
            save_path=save_graph,
            show_plot=show_graph,
            title=f"Плотность сопротивлений ({total_values} значений, {unique_count} уникальных)",
            xlabel="Сопротивление, Ом",
            ylabel="Количество точек в окне",
            label_nominals=True,
        )

    # ================================================================
    # ЗАВЕРШЕНИЕ
    # ================================================================
    elapsed = time.time() - start_time
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] ========== ПОИСК ЗАВЕРШЁН ==========")
    print(f"  Общее время: {elapsed:.2f} сек")
    print("=" * 80)

    return {
        "results": results,
        "search_results": search_results,
        "elapsed_time": elapsed,
    }