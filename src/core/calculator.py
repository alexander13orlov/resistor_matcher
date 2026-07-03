# src/core/calculator.py
# Python 3.11+
# Расчеты электрических параметров

from typing import Iterable
from .models import Resistor


def calc_series(rs: Iterable[Resistor]) -> float:
    """Последовательное соединение: сумма номиналов."""
    return sum(r.nominal for r in rs)


def calc_parallel(rs: Iterable[Resistor]) -> float:
    """Параллельное соединение: 1 / sum(1/R)."""
    inv_sum = sum(1.0 / r.nominal for r in rs)
    return 1.0 / inv_sum if inv_sum != 0 else float('inf')


def calc_tolerance_series(rs: Iterable[Resistor]) -> float:
    """
    Погрешность последовательного соединения.
    Возвращает абсолютное значение (доля от 0 до 1).
    """
    total = sum(r.nominal for r in rs)
    if total == 0:
        return 0.0
    var = sum((r.nominal * r.tolerance) ** 2 for r in rs)
    return (var ** 0.5) / total


def calc_tolerance_parallel(rs: Iterable[Resistor]) -> float:
    """
    Погрешность параллельного соединения.
    Возвращает абсолютное значение (доля от 0 до 1).
    """
    r_par = calc_parallel(rs)
    if r_par == 0 or r_par == float('inf'):
        return 0.0
    var = sum((r.tolerance / r.nominal) ** 2 for r in rs)
    return r_par * (var ** 0.5)


def format_tolerance(tol: float) -> str:
    """Форматирует погрешность в долях и процентах."""
    if tol == 0:
        return "0 (0%)"
    percent = tol * 100.0
    if percent < 0.01:
        return f"{tol:.6f} ({percent:.4f}%)"
    elif percent < 0.1:
        return f"{tol:.5f} ({percent:.3f}%)"
    elif percent < 1:
        return f"{tol:.4f} ({percent:.2f}%)"
    else:
        return f"{tol:.3f} ({percent:.1f}%)"