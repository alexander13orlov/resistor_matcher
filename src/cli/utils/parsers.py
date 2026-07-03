# src/cli/utils/parsers.py
# Парсинг аргументов

from typing import Tuple


def parse_range_nominals(value: str) -> Tuple[int, int]:
    """
    Парсит строку вида "2,3" в (2, 3).

    Args:
        value: Строка вида "N" или "N,M"

    Returns:
        Tuple[int, int]: (слева, справа)
    """
    if "," in value:
        parts = value.split(",")
        if len(parts) == 2:
            try:
                left = int(parts[0].strip())
                right = int(parts[1].strip())
                return left, right
            except ValueError:
                pass

    try:
        n = int(value.strip())
        return n, n
    except ValueError:
        return 0, 0