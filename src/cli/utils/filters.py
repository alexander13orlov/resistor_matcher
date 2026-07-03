# src/cli/utils/filters.py
# Фильтрация резисторов по соседним номиналам

from typing import List


def filter_resistors_by_nominals(
    resistor_list: List[float],
    target: float,
    left_count: int,
    right_count: int
) -> List[float]:
    """
    Фильтрует резисторы по количеству соседних номиналов.

    Args:
        resistor_list: Список номиналов (с повторениями)
        target: Целевое значение
        left_count: Сколько номиналов взять слева
        right_count: Сколько номиналов взять справа

    Returns:
        List[float]: Отфильтрованный список (с повторениями)
    """
    if left_count == 0 and right_count == 0:
        return resistor_list

    unique_nominals = sorted(set(resistor_list))

    smaller = [n for n in unique_nominals if n < target]
    larger = [n for n in unique_nominals if n > target]

    selected_smaller = smaller[-left_count:] if left_count > 0 else []
    selected_larger = larger[:right_count] if right_count > 0 else []

    selected = selected_smaller + selected_larger
    if target in unique_nominals:
        selected.append(target)

    selected_set = set(selected)
    return [r for r in resistor_list if r in selected_set]