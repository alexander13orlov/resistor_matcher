# src/cli/commands/combined_search.py
# Python 3.11+

import sys
import argparse
from typing import Optional, Dict, Any, List, Tuple

from ..main import create_parser, execute_command
from ..output.printer import print_search_results


def parse_size_arg(value: str) -> List[int]:
    """
    Парсинг --size 1,2,3,4 или 1-4
    
    Args:
        value: Строка с размерами сборок
        
    Returns:
        List[int]: Список размеров (1, 2, 3, 4)
    """
    result = []
    for part in value.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            result.extend(range(int(start), int(end) + 1))
        else:
            result.append(int(part))
    return sorted(set(result))


def get_stage_flags(size: int) -> List[str]:
    """
    Возвращает флаги для cli.main для заданного размера сборки.
    
    Args:
        size: Количество резисторов (1, 2, 3, 4)
        
    Returns:
        List[str]: Список флагов
    """
    flags_map = {
        1: ["--no-4", "--no-3", "--no-2", "--1"],
        2: ["--no-4", "--no-3", "--no-1", "--2"],
        3: ["--no-4", "--no-2", "--no-1", "--3"],
        4: ["--no-3", "--no-2", "--no-1", "--4"],
    }
    return flags_map.get(size, [])


def get_stage_name(size: int) -> str:
    """Возвращает название этапа для заданного размера."""
    names = {
        1: "ЭТАП 1: ПОИСК КОМБИНАЦИЙ ИЗ 1 РЕЗИСТОРА",
        2: "ЭТАП 2: ПОИСК КОМБИНАЦИЙ ИЗ 2 РЕЗИСТОРОВ",
        3: "ЭТАП 3: ПОИСК КОМБИНАЦИЙ ИЗ 3 РЕЗИСТОРОВ",
        4: "ЭТАП 4: ПОИСК КОМБИНАЦИЙ ИЗ 4 РЕЗИСТОРОВ",
    }
    return names.get(size, f"ЭТАП {size}: ПОИСК КОМБИНАЦИЙ ИЗ {size} РЕЗИСТОРОВ")


def run_combined_search(
    nominal: float,
    n_results: int = 5,
    size: str = "1,2,3,4",
) -> Optional[Dict[str, Any]]:
    """
    Последовательный запуск поиска для указанных размеров сборок.
    
    Args:
        nominal: Целевое сопротивление
        n_results: Количество результатов на топологию
        size: Строка с размерами сборок (например, "1,2,3,4" или "1-4")
    
    Returns:
        Optional[Dict]: Объединённые результаты
    """
    # Парсим размеры
    sizes = parse_size_arg(size)
    
    # Фильтруем только допустимые размеры (1-4)
    sizes = [s for s in sizes if 1 <= s <= 4]
    
    if not sizes:
        print("Ошибка: не указаны допустимые размеры сборок (1, 2, 3, 4)")
        return None

    all_search_results = []
    all_topo_formulas = {}
    all_results = {}
    offset = 0

    for stage_size in sizes:
        stage_name = get_stage_name(stage_size)
        
        print("\n" + "=" * 80)
        print(stage_name)
        print("=" * 80)

        # Формируем аргументы
        sys.argv = [
            "src.cli.main",
            "--nominal", str(nominal),
            "--n-results", str(n_results),
            "--optimized",
            "--auto-range",
        ] + get_stage_flags(stage_size)

        parser = create_parser()
        args = parser.parse_args()
        result = execute_command(args)

        # Проверка результата
        if result is None:
            print(f"Ошибка на этапе {stage_name}: результат отсутствует")
            continue

        if "error" in result:
            print(f"Ошибка на этапе {stage_name}: {result.get('error', 'неизвестная ошибка')}")
            continue

        # Извлекаем search_results
        search_results = result.get("search_results", [])
        results_data = result.get("results")
        if results_data is None:
            print(f"Ошибка на этапе {stage_name}: отсутствуют данные results")
            continue

        topo_formulas = results_data.get("topology_formulas", {})

        # Сохраняем результат этапа
        all_results[stage_name] = result

        # Добавляем топологии со сдвигом индексов
        for old_idx, formula in topo_formulas.items():
            all_topo_formulas[old_idx + offset] = formula

        # Добавляем search_results с коррекцией индексов
        for item in search_results:
            if len(item) >= 5:
                r_eq, values, topo_idx, tolerances, tol_total = item[:5]
                all_search_results.append((r_eq, values, topo_idx + offset, tolerances, tol_total))

        # Обновляем offset
        offset += len(topo_formulas)

    # ================================================================
    # ОБЪЕДИНЕНИЕ ВСЕХ РЕЗУЛЬТАТОВ (только если > 1 размера)
    # ================================================================
    if len(sizes) > 1:
        print("\n" + "=" * 80)
        print(f"ОБЪЕДИНЁННЫЙ РЕЗУЛЬТАТ (сборки из {', '.join(map(str, sizes))} резисторов)")
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
        "sizes": sizes,
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
    parser.add_argument(
        "--size", "-s", type=str, default="1,2,3,4",
        help="Размеры сборок: 1,2,3,4 или 1-4 (по умолчанию: 1,2,3,4)"
    )

    args = parser.parse_args()

    result = run_combined_search(
        nominal=args.nominal,
        n_results=args.n_results,
        size=args.size,
    )

    if result is not None:
        print(f"\nОбъединённые данные доступны в переменной result")
        print(f"  Сборки из {', '.join(map(str, result['sizes']))} резисторов")
        print(f"  Всего ближайших комбинаций: {len(result['combined_search'])}")