# src/analysis/topologies.py
# Python 3.11+
# Топологии соединений резисторов

from typing import List, Callable, Tuple, Dict, Any


# =====================================================================
# Топологии для 1 резистора
# =====================================================================

def topo_1_1(r: Tuple[float, ...]) -> float:
    """Один резистор: R1"""
    return r[0]

TOPOLOGIES_1: List[Callable[[Tuple[float, ...]], float]] = [topo_1_1]
TOPO_FORMULAS_1: List[str] = ["R1"]


# =====================================================================
# Топологии для 2 резисторов
# =====================================================================

def topo_2_1(r: Tuple[float, ...]) -> float:
    """Два последовательно: R1 + R2"""
    return r[0] + r[1]

def topo_2_2(r: Tuple[float, ...]) -> float:
    """Два параллельно: (R1 * R2) / (R1 + R2)"""
    return (r[0] * r[1]) / (r[0] + r[1])

TOPOLOGIES_2: List[Callable[[Tuple[float, ...]], float]] = [topo_2_1, topo_2_2]
TOPO_FORMULAS_2: List[str] = ["R1+R2", "R1||R2"]


# =====================================================================
# Топологии для 3 резисторов
# =====================================================================

def topo_3_1(r: Tuple[float, ...]) -> float:
    """Три последовательно: R1 + R2 + R3"""
    return r[0] + r[1] + r[2]

def topo_3_2(r: Tuple[float, ...]) -> float:
    """Три параллельно: 1/(1/R1 + 1/R2 + 1/R3)"""
    return 1.0 / (1.0/r[0] + 1.0/r[1] + 1.0/r[2])

def topo_3_3(r: Tuple[float, ...]) -> float:
    """Два последовательно, параллельно третьему: (R1+R2) || R3"""
    r12 = r[0] + r[1]
    return (r12 * r[2]) / (r12 + r[2])

def topo_3_4(r: Tuple[float, ...]) -> float:
    """Два параллельно, последовательно с третьим: (R1||R2) + R3"""
    r12 = (r[0] * r[1]) / (r[0] + r[1])
    return r12 + r[2]

TOPOLOGIES_3: List[Callable[[Tuple[float, ...]], float]] = [
    topo_3_1, topo_3_2, topo_3_3, topo_3_4
]
TOPO_FORMULAS_3: List[str] = [
    "R1+R2+R3",
    "1/(1/R1+1/R2+1/R3)",
    "(R1+R2)||R3",
    "(R1||R2)+R3"
]


# =====================================================================
# Топологии для 4 резисторов
# =====================================================================

def topo_4_1(r: Tuple[float, ...]) -> float:
    """Четыре последовательно: R1 + R2 + R3 + R4"""
    return r[0] + r[1] + r[2] + r[3]

def topo_4_2(r: Tuple[float, ...]) -> float:
    """Четыре параллельно: 1/(1/R1 + 1/R2 + 1/R3 + 1/R4)"""
    return 1.0 / (1.0/r[0] + 1.0/r[1] + 1.0/r[2] + 1.0/r[3])

def topo_4_3(r: Tuple[float, ...]) -> float:
    """Три последовательно, параллельно четвёртому: (R1+R2+R3) || R4"""
    r123 = r[0] + r[1] + r[2]
    return (r123 * r[3]) / (r123 + r[3])

def topo_4_4(r: Tuple[float, ...]) -> float:
    """Три параллельно, последовательно с четвёртым: (R1||R2||R3) + R4"""
    r123 = 1.0 / (1.0/r[0] + 1.0/r[1] + 1.0/r[2])
    return r123 + r[3]

def topo_4_5(r: Tuple[float, ...]) -> float:
    """Две последовательные пары параллельно: (R1+R2) || (R3+R4)"""
    r12 = r[0] + r[1]
    r34 = r[2] + r[3]
    return (r12 * r34) / (r12 + r34)

def topo_4_6(r: Tuple[float, ...]) -> float:
    """Две параллельные пары последовательно: (R1||R2) + (R3||R4)"""
    r12 = (r[0] * r[1]) / (r[0] + r[1])
    r34 = (r[2] * r[3]) / (r[2] + r[3])
    return r12 + r34

def topo_4_7(r: Tuple[float, ...]) -> float:
    """Последовательно-параллельно-последовательно: R1 + (R2||R3) + R4"""
    r23 = (r[1] * r[2]) / (r[1] + r[2])
    return r[0] + r23 + r[3]

def topo_4_8(r: Tuple[float, ...]) -> float:
    """Параллельно-последовательно-параллельно: ((R1||R2) + R3) || R4"""
    r12 = (r[0] * r[1]) / (r[0] + r[1])
    r123 = r12 + r[2]
    return (r123 * r[3]) / (r123 + r[3])

def topo_4_9(r: Tuple[float, ...]) -> float:
    """Последовательный резистор и параллель двух ветвей: R1 + (R2 || (R3+R4))"""
    r34 = r[2] + r[3]
    r234 = (r[1] * r34) / (r[1] + r34)
    return r[0] + r234

def topo_4_10(r: Tuple[float, ...]) -> float:
    """Параллельный резистор и последовательная цепочка: R1 || (R2+R3+R4)"""
    r234 = r[1] + r[2] + r[3]
    return (r[0] * r234) / (r[0] + r234)

TOPOLOGIES_4: List[Callable[[Tuple[float, ...]], float]] = [
    topo_4_1, topo_4_2, topo_4_3, topo_4_4, topo_4_5,
    topo_4_6, topo_4_7, topo_4_8, topo_4_9, topo_4_10
]

TOPO_FORMULAS_4: List[str] = [
    "R1+R2+R3+R4",
    "1/(1/R1+1/R2+1/R3+1/R4)",
    "(R1+R2+R3)||R4",
    "(R1||R2||R3)+R4",
    "(R1+R2)||(R3+R4)",
    "(R1||R2)+(R3||R4)",
    "R1+(R2||R3)+R4",
    "((R1||R2)+R3)||R4",
    "R1+(R2||(R3+R4))",
    "R1||(R2+R3+R4)"
]


# =====================================================================
# Вспомогательные функции
# =====================================================================

def get_topologies(
    include_1: bool = True,
    include_2: bool = True,
    include_3: bool = True,
    include_4: bool = True
) -> List[Tuple[Callable[[Tuple[float, ...]], float], str, int]]:
    """
    Возвращает список топологий по флагам.

    Returns:
        List[Tuple[func, formula, size]]
    """
    result: List[Tuple[Callable[[Tuple[float, ...]], float], str, int]] = []

    if include_1:
        for func, formula in zip(TOPOLOGIES_1, TOPO_FORMULAS_1):
            result.append((func, formula, 1))

    if include_2:
        for func, formula in zip(TOPOLOGIES_2, TOPO_FORMULAS_2):
            result.append((func, formula, 2))

    if include_3:
        for func, formula in zip(TOPOLOGIES_3, TOPO_FORMULAS_3):
            result.append((func, formula, 3))

    if include_4:
        for func, formula in zip(TOPOLOGIES_4, TOPO_FORMULAS_4):
            result.append((func, formula, 4))

    return result


def get_topology_count(include_1: bool = True, include_2: bool = True,
                       include_3: bool = True, include_4: bool = True) -> int:
    """Возвращает общее количество топологий."""
    return len(get_topologies(include_1, include_2, include_3, include_4))


def format_tuple(value_tuple: Tuple[float, ...]) -> str:
    """Форматирование кортежа значений для вывода."""
    return f"({', '.join(f'{v:.6g}' for v in value_tuple)})"