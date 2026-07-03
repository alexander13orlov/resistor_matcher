# src/analysis/check_series.py
# Python 3.11+
# Проверка соответствия резисторов стандартным рядам E6, E12, E24

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import FuncFormatter
from typing import List, Dict, Optional, Union, Set, Tuple
from pathlib import Path
import numpy as np
from datetime import datetime


# =====================================================================
# Стандартные ряды номиналов (строгие множества)
# =====================================================================

E6_VALUES = {1.0, 1.5, 2.2, 3.3, 4.7, 6.8}

E12_VALUES = {
    1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2
}

E24_VALUES = {
    1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
    3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1
}

SERIES_MAP = {
    'E6': E6_VALUES,
    'E12': E12_VALUES,
    'E24': E24_VALUES,
}

SERIES_ORDER = ['E24', 'E12', 'E6']


def normalize_nominal(value: float) -> float:
    """Приведение номинала к мантиссе (число от 1 до 10)."""
    if value == 0:
        return 0.0
    mantissa = value
    while mantissa < 1.0:
        mantissa *= 10.0
    while mantissa >= 10.0:
        mantissa /= 10.0
    return round(mantissa, 6)


def check_series_for_nominal(value: float) -> Dict:
    """Проверка одного номинала по всем рядам."""
    mantissa = normalize_nominal(value)
    
    return {
        'value': value,
        'mantissa': mantissa,
        'in_e6': mantissa in E6_VALUES,
        'in_e12': mantissa in E12_VALUES,
        'in_e24': mantissa in E24_VALUES,
        'in_any': mantissa in E6_VALUES or mantissa in E12_VALUES or mantissa in E24_VALUES,
    }


def get_series_color(mantissa: float) -> str:
    """
    Определение цвета для номинала.
    E24 -> светло-зелёный, E12 -> зелёный, E6 -> тёмно-зелёный, нестандартный -> красный
    """
    if mantissa in E6_VALUES:
        return '#006400'  # тёмно-зелёный
    elif mantissa in E12_VALUES:
        return '#228B22'  # лесной зелёный
    elif mantissa in E24_VALUES:
        return '#90EE90'  # светло-зелёный
    else:
        return '#FF0000'  # красный


def get_series_label(mantissa: float) -> str:
    """Возвращает метку ряда для номинала."""
    if mantissa in E6_VALUES:
        return 'E6'
    elif mantissa in E12_VALUES:
        return 'E12'
    elif mantissa in E24_VALUES:
        return 'E24'
    else:
        return 'нестандартный'


def check_resistor_file(
    filepath: Union[str, Path],
    sheet_name: Union[int, str] = 0,
    value_column: str = "Номинал",
    skip_zero: bool = True,
    skip_negative: bool = True
) -> Dict:
    """Проверка всех резисторов из Excel-файла."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Файл не найден: {filepath}")
    
    df = pd.read_excel(filepath, sheet_name=sheet_name, engine='openpyxl')
    df.columns = df.columns.str.strip()
    
    if value_column not in df.columns:
        raise KeyError(f"Столбец '{value_column}' не найден.")
    
    values = []
    for _, row in df.iterrows():
        val = row[value_column]
        if pd.isna(val):
            continue
        try:
            val_float = float(val)
            if skip_zero and val_float == 0:
                continue
            if skip_negative and val_float < 0:
                continue
            values.append(val_float)
        except (ValueError, TypeError):
            continue
    
    results = []
    unique_values = set(values)
    
    # Статистика по всем резисторам (с повторениями)
    membership_counts_all = {
        'E6': 0,
        'E12': 0,
        'E24': 0,
        'none': 0,
    }
    
    # Статистика по уникальным номиналам
    membership_counts_unique = {
        'E6': 0,
        'E12': 0,
        'E24': 0,
        'none': 0,
    }
    
    # Подсчёт количества каждого номинала
    value_counts = {}
    for val in values:
        value_counts[val] = value_counts.get(val, 0) + 1
    
    # Результаты для всех резисторов
    for val in values:
        result = check_series_for_nominal(val)
        results.append(result)
        
        if result['in_e6']:
            membership_counts_all['E6'] += 1
        if result['in_e12']:
            membership_counts_all['E12'] += 1
        if result['in_e24']:
            membership_counts_all['E24'] += 1
        if not result['in_any']:
            membership_counts_all['none'] += 1
    
    # Результаты для уникальных номиналов
    for val in unique_values:
        result = check_series_for_nominal(val)
        
        if result['in_e6']:
            membership_counts_unique['E6'] += 1
        if result['in_e12']:
            membership_counts_unique['E12'] += 1
        if result['in_e24']:
            membership_counts_unique['E24'] += 1
        if not result['in_any']:
            membership_counts_unique['none'] += 1
    
    # Уникальные нестандартные номиналы (только для внутреннего использования)
    nonstandard_unique = sorted([
        v for v in unique_values 
        if not check_series_for_nominal(v)['in_any']
    ])
    
    # Данные для графика: номиналы и их частоты
    sorted_unique = sorted(unique_values)
    frequencies = [value_counts[v] for v in sorted_unique]
    colors = [get_series_color(normalize_nominal(v)) for v in sorted_unique]
    labels = [get_series_label(normalize_nominal(v)) for v in sorted_unique]
    
    return {
        'total_count': len(values),
        'unique_count': len(unique_values),
        'results': results,
        'membership_counts_all': membership_counts_all,
        'membership_counts_unique': membership_counts_unique,
        'nonstandard_unique': nonstandard_unique,
        'value_counts': value_counts,
        'sorted_unique': sorted_unique,
        'frequencies': frequencies,
        'colors': colors,
        'labels': labels,
    }


def print_series_report(stats: Dict) -> None:
    """Вывод отчёта о соответствии рядам."""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА СООТВЕТСТВИЯ РЯДАМ E6 / E12 / E24")
    print("=" * 70)
    
    total = stats['total_count']
    unique = stats['unique_count']
    counts_all = stats['membership_counts_all']
    counts_unique = stats['membership_counts_unique']
    
    print(f"\nВсего резисторов (с повторениями): {total}")
    print(f"Уникальных номиналов: {unique}")
    
    # Статистика по всем резисторам
    print("\n" + "-" * 70)
    print("СТАТИСТИКА ПО ВСЕМ РЕЗИСТОРАМ (с повторениями):")
    print("-" * 70)
    print(f"{'Ряд':<6} {'Количество':<15} {'Процент':<10}")
    print("-" * 70)
    
    for series_name in SERIES_ORDER:
        count = counts_all[series_name]
        print(
            f"{series_name:<6} "
            f"{count:<15} "
            f"{(count / total * 100):>6.1f}%"
        )
    
    none_count = counts_all['none']
    print(
        f"{'None':<6} "
        f"{none_count:<15} "
        f"{(none_count / total * 100):>6.1f}%"
    )
    
    # Статистика по уникальным номиналам
    print("\n" + "-" * 70)
    print("СТАТИСТИКА ПО УНИКАЛЬНЫМ НОМИНАЛАМ:")
    print("-" * 70)
    print(f"{'Ряд':<6} {'Количество':<15} {'Процент':<10}")
    print("-" * 70)
    
    for series_name in SERIES_ORDER:
        count = counts_unique[series_name]
        print(
            f"{series_name:<6} "
            f"{count:<15} "
            f"{(count / unique * 100):>6.1f}%"
        )
    
    none_count_unique = counts_unique['none']
    print(
        f"{'None':<6} "
        f"{none_count_unique:<15} "
        f"{(none_count_unique / unique * 100):>6.1f}%"
    )
    
    # Сводка
    print("\n" + "=" * 70)
    print("СВОДКА:")
    print("=" * 70)
    
    if none_count == 0:
        print("  ✅ Все резисторы принадлежат хотя бы одному ряду")
    else:
        print(f"  ⚠ {none_count} резисторов ({none_count/total*100:.1f}%) НЕ принадлежат ни одному ряду")
    
    if none_count_unique == 0:
        print("  ✅ Все уникальные номиналы принадлежат хотя бы одному ряду")
    else:
        print(f"  ⚠ {none_count_unique} уникальных номиналов ({none_count_unique/unique*100:.1f}%) НЕ принадлежат ни одному ряду")
    
    for series_name in SERIES_ORDER:
        count = counts_all[series_name]
        print(f"  Ряд {series_name}: {count} резисторов ({count/total*100:.1f}%)")
    
    print("=" * 70)


def format_nominal_label(value: float) -> str:
    """
    Форматирует номинал для отображения на графике.
    Убирает незначащие нули, использует компактный формат.
    
    Примеры:
        100.0 -> 100
        1000.0 -> 1k
        0.002 -> 0.002
        0.02 -> 0.02
        0.2 -> 0.2
        2.0 -> 2
        2.2 -> 2.2
    """
    if value >= 1000:
        return f'{value/1000:.0f}k'
    elif value >= 1:
        if value == int(value):
            return f'{int(value)}'
        else:
            s = f'{value:.3f}'.rstrip('0').rstrip('.')
            return s
    else:
        s = f'{value:.3f}'.rstrip('0').rstrip('.')
        return s


def plot_series_distribution(
    stats: Dict,
    save_path: Optional[Union[str, Path]] = None,
    show_plot: bool = True,
    figsize: Tuple[int, int] = (16, 10),
    dpi: int = 150,
    log_x: bool = False,
    log_y: bool = False,
    label_threshold: float = 0.2,
    label_fontsize: int = 8,
    label_rotation: float = 0
) -> None:
    """
    Построение графика распределения номиналов.
    
    Args:
        stats: Статистика из check_resistor_file
        save_path: Путь для сохранения графика
        show_plot: Показывать график
        figsize: Размер фигуры
        dpi: Разрешение при сохранении
        log_x: Логарифмическая шкала по оси X (по умолчанию: True)
        log_y: Логарифмическая шкала по оси Y (по умолчанию: False)
        label_threshold: Порог для подписей (доля от максимальной высоты)
        label_fontsize: Размер шрифта подписей
        label_rotation: Поворот подписей (по умолчанию: 90 градусов)
    """
    sorted_unique = stats['sorted_unique']
    frequencies = stats['frequencies']
    colors = stats['colors']
    
    # Создаём легенду
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#006400', label='E6'),
        Patch(facecolor='#228B22', label='E12'),
        Patch(facecolor='#90EE90', label='E24'),
        Patch(facecolor='#FF0000', label='нестандартный'),
    ]
    
    fig, ax = plt.subplots(figsize=figsize)
    
    max_freq = max(frequencies) if frequencies else 1
    threshold = max_freq * label_threshold
    
    # Если логарифмическая шкала по X
    if log_x:
        log_values = np.log10(sorted_unique)
        
        if len(log_values) > 1:
            widths = np.diff(log_values)
            widths = np.append(widths, widths[-1])
        else:
            widths = [0.1]
        
        # Рисуем столбцы
        for i, (val, freq, color, log_val) in enumerate(zip(sorted_unique, frequencies, colors, log_values)):
            ax.bar(
                val,
                freq,
                width=0.8 * (10**widths[i] - 1) * val,
                color=color,
                edgecolor='black',
                linewidth=0.5,
                alpha=0.8,
                align='center'
            )
            
            # Подпись сверху для высоких столбцов — номинал
            if freq >= threshold:
                label_text = format_nominal_label(val)
                
                ax.text(
                    val,
                    freq * 1.02,
                    label_text,
                    ha='center',
                    va='bottom',
                    fontsize=label_fontsize,
                    fontweight='bold',
                    color='black',
                    rotation=label_rotation
                )
        
        ax.set_xscale('log')
        ax.set_xlabel('Номинал, Ом (логарифмическая шкала)', fontsize=12)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.3g}'))
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        
    else:
        # Линейная шкала — обычные столбцы
        bars = ax.bar(
            range(len(sorted_unique)),
            frequencies,
            color=colors,
            edgecolor='black',
            linewidth=0.5,
            alpha=0.8
        )
        
        # Подписи сверху для высоких столбцов — номинал
        for i, (bar, freq, val) in enumerate(zip(bars, frequencies, sorted_unique)):
            if freq >= threshold:
                label_text = format_nominal_label(val)
                
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    freq * 1.02,
                    label_text,
                    ha='center',
                    va='bottom',
                    fontsize=label_fontsize,
                    fontweight='bold',
                    color='black',
                    rotation=label_rotation
                )
        
        # Подписи оси X
        step = max(1, len(sorted_unique) // 30)
        x_labels = []
        for i, v in enumerate(sorted_unique):
            if i % step == 0:
                x_labels.append(format_nominal_label(v))
            else:
                x_labels.append("")
        
        ax.set_xticks(range(len(sorted_unique)))
        ax.set_xticklabels(x_labels, rotation=90, fontsize=7)
        ax.set_xlabel('Номинал, Ом', fontsize=12)
    
    # Логарифмическая шкала по Y
    if log_y:
        ax.set_yscale('log')
        ax.set_ylabel('Количество (логарифмическая шкала)', fontsize=12)
    else:
        ax.set_ylabel('Количество', fontsize=12)
    
    ax.set_title(f'Распределение номиналов резисторов\n(всего {stats["total_count"]} шт., уникальных {stats["unique_count"]})', fontsize=14)
    
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    
    fig.tight_layout()
    
    if save_path:
        save_path = Path(save_path)
        if save_path.is_dir():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = ""
            if log_x:
                suffix += "_logx"
            if log_y:
                suffix += "_logy"
            save_path = save_path / f"series_distribution{suffix}_{timestamp}.png"
        else:
            save_path.parent.mkdir(parents=True, exist_ok=True)
        
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        print(f"\nГрафик сохранён: {save_path}")
    
    if show_plot:
        plt.show()
    
    plt.close(fig)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    filepath = Path(__file__).parent.parent.parent / "db" / "resistor.xlsx"
    
    if not filepath.exists():
        print(f"Файл не найден: {filepath}")
        sys.exit(1)
    
    stats = check_resistor_file(
        filepath=filepath,
        value_column="Номинал"
    )
    
    print_series_report(stats)
    # print_nonstandard_report(stats)  # Убрано — не выводим список нестандартных номиналов
    
    # Построение графика с подписями номиналов сверху
    plot_series_distribution(
        stats,
        save_path=Path(__file__).parent.parent.parent / "img",
        show_plot=True,
        log_x=False,
        log_y=False,
        label_threshold=0.3,
        label_fontsize=8,
        label_rotation=0
    )