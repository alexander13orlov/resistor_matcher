# src/cli/commands/analyze.py
# Полный анализ с графиком плотности

import time
from typing import Optional, Dict, Union
from pathlib import Path

from ...core.loader import load_resistor_values_from_excel
from ...analysis.combiner import analyze_resistor_combinations
from ...viz.density import plot_density


def run_analyze(
    filepath: Union[str, Path],
    precision: int = 3,
    max_repeats: int = 4,
    inc4: bool = True,
    inc3: bool = True,
    inc2: bool = True,
    inc1: bool = True,
    save_graph: Optional[str] = "img/",
    show_graph: bool = True,
    show_details: bool = False,
    details_limit: int = 100,
) -> Dict:
    """
    Полный анализ: комбинации + график плотности.
    """
    start_time = time.time()
    timestamp_start = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp_start}] ========== ПОЛНЫЙ АНАЛИЗ ==========")

    # Загрузка
    try:
        resistor_list = load_resistor_values_from_excel(
            filepath, max_repeats_per_nominal=max_repeats
        )
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка загрузки: {e}")
        return {"error": str(e)}

    if not resistor_list:
        print("Ошибка: нет резисторов")
        return {"error": "no_resistors"}

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Количество резисторов: {len(resistor_list)}")
    source_nominals = sorted(set(resistor_list))

    # Анализ
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Анализ комбинаций...")
    results = analyze_resistor_combinations(
        resistor_list,
        round_precision=precision,
        include_4=inc4,
        include_3=inc3,
        include_2=inc2,
        include_1=inc1,
        verbose_details=show_details,
        verbose_details_limit=details_limit,
    )

    total_values = results["total_values"]
    unique_count = results["unique_count"]
    all_values = results["all_values_sorted"]

    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Результаты:")
    print(f"  Всего размещений: {results['total_arrangements']}")
    print(f"  Уникальных кортежей: {results['unique_value_tuples']}")
    print(f"  Всего значений: {total_values}")
    print(f"  Уникальных значений: {unique_count}")

    if all_values:
        print(f"  Диапазон: [{all_values[0]:.6g} ... {all_values[-1]:.6g}]")

    # Статистика по топологиям
    if results.get("topology_unique_counts"):
        print(f"\n  Статистика по топологиям:")
        print(f"  {'-' * 70}")
        for name, count in results["topology_unique_counts"].items():
            print(f"  {name}: {count} уник.")
        print(f"  {'-' * 70}")

    # График
    if total_values > 0:
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Построение графика плотности...")
        plot_density(
            all_values,
            source_nominals=source_nominals,
            save_path=save_graph,
            show_plot=show_graph,
            title=f"Плотность сопротивлений ({total_values} значений, {unique_count} уникальных)",
            xlabel="Сопротивление, Ом",
            ylabel="Количество точек в окне",
            label_nominals=True,
        )

    elapsed = time.time() - start_time
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] ========== АНАЛИЗ ЗАВЕРШЁН ==========")
    print(f"  Общее время: {elapsed:.2f} сек")
    print("=" * 80)

    return {"results": results, "elapsed_time": elapsed}