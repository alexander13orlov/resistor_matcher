# src/cli/commands/combined_search.py
# Python 3.11+
# Обёртка для последовательного поиска комбинаций из 1, 2, 3 и 4 резисторов

import sys
import argparse
from typing import Optional, Dict, Any, List, Tuple

from ..main import create_parser, execute_command
from ..output.printer import print_search_results


def run_combined_search(
    nominal: float,
    n_results: int = 5,
) -> Optional[Dict[str, Any]]:
    """
    Последовательный запуск поиска для 1, 2, 3 и 4 резисторов.

    Args:
        nominal: Целевое сопротивление
        n_results: Количество результатов на топологию

    Returns:
        Optional[Dict]: Объединённые результаты
    """
    # Определение этапов
    stages = [
        {
            "name": "ЭТАП 1: ПОИСК КОМБИНАЦИЙ ИЗ 1 РЕЗИСТОРА",
            "flags": ["--no-4", "--no-3", "--no-2", "--1"],
        },
        {
            "name": "ЭТАП 2: ПОИСК КОМБИНАЦИЙ ИЗ 2 РЕЗИСТОРОВ",
            "flags": ["--no-4", "--no-3", "--no-1", "--2"],
        },
        {
            "name": "ЭТАП 3: ПОИСК КОМБИНАЦИЙ ИЗ 3 РЕЗИСТОРОВ",
            "flags": ["--no-4", "--no-2", "--no-1", "--3"],
        },
        {
            "name": "ЭТАП 4: ПОИСК КОМБИНАЦИЙ ИЗ 4 РЕЗИСТОРОВ",
            "flags": ["--no-3", "--no-2", "--no-1", "--4"],
        },
    ]

    all_search_results = []
    all_topo_formulas = {}
    all_results = {}
    offset = 0

    for stage in stages:
        print("\n" + "=" * 80)
        print(stage["name"])
        print("=" * 80)

        # Формируем аргументы
        sys.argv = [
            "src.cli.main",
            "--nominal", str(nominal),
            "--n-results", str(n_results),
            "--optimized",
            "--auto-range",
        ] + stage["flags"]

        parser = create_parser()
        args = parser.parse_args()
        result = execute_command(args)

        # Проверка результата на None и наличие ошибки
        if result is None:
            print(f"Ошибка на этапе {stage['name']}: результат отсутствует")
            continue

        if "error" in result:
            print(f"Ошибка на этапе {stage['name']}: {result.get('error', 'неизвестная ошибка')}")
            continue

        # Извлекаем search_results (отфильтрованные 10 слева + 10 справа)
        search_results = result.get("search_results", [])
        results_data = result.get("results")
        if results_data is None:
            print(f"Ошибка на этапе {stage['name']}: отсутствуют данные results")
            continue

        topo_formulas = results_data.get("topology_formulas", {})

        # Сохраняем полный результат этапа
        all_results[stage["name"]] = result

        # Добавляем топологии со сдвигом индексов
        for old_idx, formula in topo_formulas.items():
            all_topo_formulas[old_idx + offset] = formula

        # Добавляем search_results с коррекцией индексов
        for item in search_results:
            # Ожидаемая структура: (r_eq, values, topo_idx, tolerances, tol_total)
            if len(item) >= 5:
                r_eq, values, topo_idx, tolerances, tol_total = item[:5]
                all_search_results.append((r_eq, values, topo_idx + offset, tolerances, tol_total))
            else:
                # fallback, если структура неполная
                all_search_results.append(item)

        # Обновляем offset для следующего этапа
        offset += len(topo_formulas)

    # ================================================================
    # ОБЪЕДИНЕНИЕ ВСЕХ РЕЗУЛЬТАТОВ
    # ================================================================
    print("\n" + "=" * 80)
    print("ОБЪЕДИНЁННЫЙ РЕЗУЛЬТАТ (1 + 2 + 3 + 4 РЕЗИСТОРА) — ТОЛЬКО БЛИЖАЙШИЕ")
    print("=" * 80)

    # Сортировка по R_экв
    all_search_results.sort(key=lambda x: x[0])

    # Вывод объединённой таблицы
    print_search_results(
        all_search_results,
        all_topo_formulas,
        target=nominal
    )

    # ================================================================
    # ВОЗВРАТ ДАННЫХ
    # ================================================================
    return {
        "all_results": all_results,
        "combined_search": all_search_results,
        "topo_formulas": all_topo_formulas,
        "nominal": nominal,
        "n_results": n_results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Последовательный поиск комбинаций из 1, 2, 3 и 4 резисторов"
    )
    parser.add_argument(
        "--nominal", "-n", type=float, required=True,
        help="Целевое сопротивление"
    )
    parser.add_argument(
        "--n-results", "-nr", type=int, default=5,
        help="Количество результатов на топологию (по умолчанию: 5)"
    )

    args = parser.parse_args()

    result = run_combined_search(
        nominal=args.nominal,
        n_results=args.n_results,
    )

    if result is not None:
        print(f"\nОбъединённые данные доступны в переменной result")
        print(f"  Всего ближайших комбинаций: {len(result['combined_search'])}")