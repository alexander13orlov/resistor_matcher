# src/cli/output/printer.py
# Вывод результатов в консоль

from typing import List, Tuple, Dict, Optional, Union, Any
from .formatter import format_deviation


def format_tolerances_list(tolerances: Any) -> str:
    """Форматирует список точностей в компактный вид."""
    if tolerances is None:
        return "—"
    
    if isinstance(tolerances, (list, tuple)):
        tol_tuple = tuple(tolerances)
    else:
        return "—"
    
    if not tol_tuple:
        return "—"
    
    if len(tol_tuple) > 1 and len(set(tol_tuple)) == 1:
        return f"±{tol_tuple[0]*100:.1f}% x{len(tol_tuple)}"
    
    return "[" + ", ".join([f"{t*100:.1f}%" for t in tol_tuple]) + "]"


def format_deviation_high_precision(value: float, target: float) -> str:
    """Форматирует отклонение с высокой точностью (до 6 знаков)."""
    if target == 0:
        return "---"
    dev = abs(value - target) / target * 100
    if dev < 0.000001:
        return "< 0.000001%"
    elif dev < 0.00001:
        return f"{dev:.6f}%"
    elif dev < 0.0001:
        return f"{dev:.5f}%"
    elif dev < 0.001:
        return f"{dev:.4f}%"
    elif dev < 0.01:
        return f"{dev:.3f}%"
    elif dev < 0.1:
        return f"{dev:.2f}%"
    else:
        return f"{dev:.1f}%"


def print_search_results(
    results: List[Tuple[float, Tuple[float, ...], int, Tuple[float, ...], float]],
    topo_formulas: Dict[int, str],
    highlight_idx: Optional[Union[int, List[int]]] = None,
    target: Optional[float] = None
) -> None:
    """
    Вывод результатов поиска в консоль с указанием отклонения и точностей.
    
    Args:
        highlight_idx: Индекс или список индексов для подсветки (<--).
    """
    from ...analysis.topologies import format_tuple

    if not results:
        print("  Результатов не найдено.")
        return

    # Если highlight_idx — одно число, превращаем в список
    if isinstance(highlight_idx, int):
        highlight_indices = {highlight_idx}
    elif isinstance(highlight_idx, list):
        highlight_indices = set(highlight_idx)
    else:
        highlight_indices = set()

    print(f"\n  Найдено {len(results)} значений:")
    print(f"  {'-' * 120}")
    print(f"{'#':<4} {'R_экв, Ом':<14} {'Отклонение':<14} {'Схема':<30} {'Номиналы':<22} {'Точность вх.':<18} {'Точность сб.':<12}")
    print(f"  {'-' * 120}")

    for idx, item in enumerate(results):
        try:
            r_eq = item[0]
            v_tuple = item[1]
            topo_idx = item[2]
            tolerances = item[3] if len(item) > 3 else ()
            tol_total = item[4] if len(item) > 4 else 0.0
        except (IndexError, ValueError):
            continue

        formula = topo_formulas.get(topo_idx, f"Схема {topo_idx + 1}")
        marker = " <--" if idx in highlight_indices else ""

        if target is not None:
            dev_str = format_deviation_high_precision(r_eq, target)
        else:
            dev_str = "---"

        if len(formula) > 28:
            formula = formula[:25] + "..."

        nominal_str = format_tuple(v_tuple)

        tol_in_str = format_tolerances_list(tolerances)
        tol_out_str = f"{tol_total*100:.2f}%" if tol_total > 0 else "—"

        print(
            f"  {idx + 1:<4} {r_eq:<14.6f} {dev_str:<14} {formula:<30} {nominal_str:<22} {tol_in_str:<18} {tol_out_str:<12}{marker}"
        )

    print(f"  {'-' * 120}")