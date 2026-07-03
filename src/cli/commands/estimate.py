# src/cli/commands/estimate.py
# Оценка вычислительной сложности

import math
from typing import Optional, Dict, Union
from pathlib import Path

from ...core.loader import load_resistor_values_from_excel
from ..utils import parse_range_nominals, filter_resistors_by_nominals


def permutations_count(n: int, k: int) -> int:
    """A(n,k) = n! / (n-k)!"""
    if k > n:
        return 0
    result = 1
    for i in range(n, n - k, -1):
        result *= i
    return result


def estimate_unique_tuples(n: int, k: int, unique_nominals: int) -> tuple:
    """Оценка количества уникальных кортежей."""
    upper = min(permutations_count(n, k), unique_nominals ** k)
    lower = min(upper, math.comb(unique_nominals, k) if unique_nominals >= k else 0)
    return lower, upper


def estimate_memory(values_count: int) -> str:
    """Оценка потребляемой памяти."""
    bytes_per_value = 72
    total = values_count * bytes_per_value
    if total < 1024:
        return f"{total} Б"
    elif total < 1024 ** 2:
        return f"{total / 1024:.1f} КБ"
    elif total < 1024 ** 3:
        return f"{total / 1024 ** 2:.1f} МБ"
    else:
        return f"{total / 1024 ** 3:.2f} ГБ"


def estimate_time(total_ops: int) -> str:
    """Оценка времени выполнения."""
    ops_per_second = 50000
    seconds = total_ops / ops_per_second
    if seconds < 1:
        return "< 1 сек"
    elif seconds < 60:
        return f"{seconds:.0f} сек"
    elif seconds < 3600:
        return f"{seconds / 60:.1f} мин"
    else:
        return f"{seconds / 3600:.1f} ч"


def run_estimate(
    filepath: Union[str, Path],
    max_repeats: int = 4,
    range_nominals: Optional[str] = None,
    inc4: bool = True,
    inc3: bool = True,
    inc2: bool = True,
    inc1: bool = True,
) -> Dict:
    """
    Оценка вычислительной сложности анализа.
    """
    print("=" * 70)
    print("ОЦЕНКА ВЫЧИСЛИТЕЛЬНОЙ СЛОЖНОСТИ")
    print("=" * 70)

    try:
        resistor_list = load_resistor_values_from_excel(
            filepath, max_repeats_per_nominal=max_repeats
        )
    except Exception as e:
        print(f"\nОшибка загрузки: {e}")
        return {"error": str(e)}

    n = len(resistor_list)
    unique_nominals = len(set(resistor_list))

    if n == 0:
        print("\nОшибка: нет резисторов")
        return {"error": "no_resistors"}

    # Фильтрация по соседним номиналам
    if range_nominals:
        left, right = parse_range_nominals(range_nominals)
        filtered = filter_resistors_by_nominals(
            resistor_list,
            sorted(set(resistor_list))[len(set(resistor_list)) // 2],
            left, right
        )
        print(f"\nФильтрация по соседним номиналам:")
        print(f"  Было резисторов: {n}")
        print(f"  Было уникальных: {unique_nominals}")
        n = len(filtered)
        unique_nominals = len(set(filtered))
        print(f"  Стало резисторов: {n}")
        print(f"  Стало уникальных: {unique_nominals}")
        print(f"  Взято слева: {left}, справа: {right}")

    # Топологии
    topo_counts = {}
    if inc1:
        topo_counts[1] = 1
    if inc2:
        topo_counts[2] = 2
    if inc3:
        topo_counts[3] = 4
    if inc4:
        topo_counts[4] = 10

    if not topo_counts:
        print("\nОшибка: не выбрано ни одной схемы")
        return {"error": "no_topologies"}

    total_topo = sum(topo_counts.values())

    print(f"\n{'=' * 70}")
    print(f"Исходные данные:")
    print(f"  Резисторов: {n:,}")
    print(f"  Уникальных номиналов: {unique_nominals:,}")
    print(f"  Схемы: {', '.join(f'{k} рез. ({v} топ.)' for k, v in sorted(topo_counts.items()))}")
    print(f"  Всего топологий: {total_topo}")

    # Оценка размещений
    print(f"\n{'=' * 70}")
    print("Оценка размещений A(n,k):")
    print("=" * 70)

    total_perm = 0
    total_lower = 0
    total_upper = 0

    for k in sorted(topo_counts.keys()):
        if k > n:
            print(f"  A({n},{k}): недостаточно резисторов")
            continue

        perm = permutations_count(n, k)
        total_perm += perm
        lower, upper = estimate_unique_tuples(n, k, unique_nominals)
        total_lower += lower
        total_upper += upper

        print(f"  A({n},{k}) = {perm:,} размещений")
        print(f"    Уник. кортежей: {lower:,} – {upper:,}")

    print(f"\n  Всего размещений: {total_perm:,}")
    print(f"  Уник. кортежей: {total_lower:,} – {total_upper:,}")

    # Оценка итогового ряда
    values_lower = total_lower * total_topo
    values_upper = total_upper * total_topo
    values_filtered = int(values_upper * 0.7)

    print(f"\n{'=' * 70}")
    print("Оценка итогового ряда:")
    print("=" * 70)
    print(f"  Кортежей × топологий:")
    print(f"    Минимум: {total_lower:,} × {total_topo} = {values_lower:,}")
    print(f"    Максимум: {total_upper:,} × {total_topo} = {values_upper:,}")
    print(f"    После фильтрации (~70%): ~{values_filtered:,}")

    print(f"\n  Память (макс): {estimate_memory(values_upper)}")
    print(f"  Память (после фильтрации): {estimate_memory(values_filtered)}")

    # Время
    total_ops = total_upper * total_topo
    print(f"\n{'=' * 70}")
    print("Оценка времени:")
    print("=" * 70)
    print(f"  Оценочное время (min): {estimate_time(int(values_lower * 1.5))}")
    print(f"  Оценочное время (max): {estimate_time(int(total_ops))}")

    # Рекомендации
    print(f"\n{'=' * 70}")
    print("Рекомендации:")
    print("=" * 70)

    warnings = []
    if total_perm > 10_000_000:
        warnings.append("Очень много размещений (>10M). Уменьшите max_repeats до 2-3.")
    if values_upper > 10_000_000:
        warnings.append("Итоговый ряд >10M значений. Возможна нехватка памяти.")
    if unique_nominals > 100 and n > 200:
        warnings.append("Много уникальных номиналов. Отключите схемы из 4 резисторов.")

    if warnings:
        for w in warnings:
            print(f"  ⚠ {w}")
    else:
        print("  Объём данных приемлемый.")

    print(f"\n{'=' * 70}")
    print("СВОДКА:")
    print("=" * 70)
    print(f"  Резисторов:            {n:,}")
    print(f"  Уникальных номиналов:   {unique_nominals:,}")
    print(f"  Размещений:             {total_perm:,}")
    print(f"  Уник. кортежей:         {total_lower:,} – {total_upper:,}")
    print(f"  Топологий:              {total_topo}")
    print(f"  Значений (оценка):      {values_filtered:,}")
    print(f"  Память:                 {estimate_memory(values_filtered)}")
    print(f"  Время (оценка):         {estimate_time(int(values_filtered * 1.5))}")
    print("=" * 70)

    return {
        "n": n,
        "unique_nominals": unique_nominals,
        "values_filtered": values_filtered,
    }