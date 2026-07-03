# src/cli/output/formatter.py
# Форматирование данных для вывода


def format_deviation(value: float, target: float) -> str:
    """Форматирует отклонение в процентах."""
    if target == 0:
        return "---"
    dev = abs(value - target) / target * 100
    if dev < 0.001:
        return "< 0.001%"
    elif dev < 0.01:
        return f"{dev:.3f}%"
    elif dev < 0.1:
        return f"{dev:.2f}%"
    elif dev < 1:
        return f"{dev:.2f}%"
    else:
        return f"{dev:.1f}%"


def format_nominal_label(value: float) -> str:
    """
    Форматирует номинал для отображения на графике.
    Убирает незначащие нули.
    """
    if value >= 1000:
        return f"{value/1000:.0f}k"
    elif value >= 1:
        if value == int(value):
            return f"{int(value)}"
        else:
            s = f"{value:.3f}".rstrip("0").rstrip(".")
            return s
    else:
        s = f"{value:.3f}".rstrip("0").rstrip(".")
        return s