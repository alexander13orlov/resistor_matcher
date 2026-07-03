# src/viz/density.py
# Python 3.11+
# Построение графика локальной плотности точек числового ряда

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
from typing import Tuple, Optional, Sequence, List, Union
from pathlib import Path
import time
from datetime import datetime


def compute_local_density(
    values: Sequence[float],
    window: Optional[float] = None,
    window_type: str = "relative"
) -> Tuple[np.ndarray, np.ndarray]:
    """Вычисление локальной плотности точек ряда."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] compute_local_density: старт, количество точек: {len(values)}")
    
    sorted_vals = np.sort(np.array(values, dtype=np.float64))
    n = len(sorted_vals)
    
    if n == 0:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] compute_local_density: пустой вход")
        return np.array([]), np.array([])
    
    min_val = sorted_vals[0]
    max_val = sorted_vals[-1]
    value_range = max_val - min_val
    
    if window is None:
        window_param = 0.05
    else:
        window_param = window
    
    density = np.zeros(n, dtype=np.int32)
    
    if window_type == "absolute":
        absolute_window = window_param
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] compute_local_density: режим absolute, окно={absolute_window:.4f}")
        
        left = 0
        right = 0
        for i in range(n):
            center = sorted_vals[i]
            left_bound = center - absolute_window
            right_bound = center + absolute_window
            
            while left < i and sorted_vals[left] < left_bound:
                left += 1
            while right < n and sorted_vals[right] <= right_bound:
                right += 1
            
            density[i] = right - left
    
    elif window_type == "fraction":
        if value_range == 0:
            absolute_window = 1.0
        else:
            absolute_window = value_range * window_param
        
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] compute_local_density: режим fraction, окно={absolute_window:.4f}")
        
        left = 0
        right = 0
        for i in range(n):
            center = sorted_vals[i]
            left_bound = center - absolute_window
            right_bound = center + absolute_window
            
            while left < i and sorted_vals[left] < left_bound:
                left += 1
            while right < n and sorted_vals[right] <= right_bound:
                right += 1
            
            density[i] = right - left
    
    else:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] compute_local_density: режим relative, окно={window_param*100:.1f}% от текущего x")
        
        for i in range(n):
            center = sorted_vals[i]
            
            if abs(center) < 1e-12:
                half_window = window_param * 1e-9
            else:
                half_window = window_param * abs(center)
            
            left_bound = center - half_window
            right_bound = center + half_window
            
            left = np.searchsorted(sorted_vals, left_bound, side='left')
            right = np.searchsorted(sorted_vals, right_bound, side='right')
            
            density[i] = right - left
    
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] compute_local_density: плотность min={density.min()}, max={density.max()}")
    
    return sorted_vals, density


def plot_density(
    values: Sequence[float],
    source_nominals: Optional[Sequence[float]] = None,
    window: Optional[float] = None,
    window_type: str = "relative",
    title: Optional[str] = "Плотность",
    xlabel: str = "Сопротивление, Ом",
    ylabel: str = "Количество точек в окне",
    figsize: Tuple[int, int] = (14, 7),
    grid: bool = True,
    grid_alpha: float = 0.3,
    grid_which: str = "both",
    color: str = "steelblue",
    marker_size: int = 4,
    alpha: float = 0.7,
    save_path: Optional[Union[str, Path]] = None,
    dpi: int = 150,
    force_log_x: bool = False,
    force_log_y: bool = False,
    show_plot: bool = True,
    label_nominals: bool = True,
    label_min_distance: float = 0.05,
    label_fontsize: int = 7,
    label_rotation: float = 0,
    label_y_offset: float = 0.08
) -> Figure:
    """
    Построение графика локальной плотности точек ряда.
    
    Args:
        values: Входной ряд чисел
        source_nominals: Исходные уникальные номиналы для отметки красными линиями
        window: Параметр окна
        window_type: "relative", "absolute", "fraction"
        title: Заголовок графика (по умолчанию: "Плотность значений")
        xlabel: Подпись оси X (по умолчанию: "Сопротивление, Ом")
        ylabel: Подпись оси Y (по умолчанию: "Количество точек в окне")
        figsize: Размер фигуры
        grid: Показывать сетку
        grid_alpha: Прозрачность сетки
        grid_which: Какие линии сетки ("major", "minor", "both")
        color: Цвет маркеров плотности
        marker_size: Размер маркеров
        alpha: Прозрачность маркеров
        save_path: Путь для сохранения
        dpi: Разрешение при сохранении
        force_log_x: Принудительно включить логарифмическую шкалу по X
        force_log_y: Принудительно включить логарифмическую шкалу по Y
        show_plot: Показывать график
        label_nominals: Подписывать номиналы на красных линиях
        label_min_distance: Минимальное расстояние между подписями
        label_fontsize: Размер шрифта подписей
        label_rotation: Поворот подписей (градусы)
        label_y_offset: Смещение подписи вверх (в долях от диапазона Y)
    """
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] plot_density: построение графика")
    
    x, density = compute_local_density(values, window, window_type)
    
    if len(x) == 0:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "Нет данных", ha='center', va='center', transform=ax.transAxes)
        if save_path:
            fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        return fig
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Формирование метки окна
    if window is None:
        window_label = "5% от x"
    elif window_type == "absolute":
        window_label = f"{window}"
    elif window_type == "fraction":
        window_label = f"{window * 100:.0f}% диапазона"
    else:
        window_label = f"{window * 100:.0f}% от x"
    
    # Основной график плотности
    ax.scatter(
        x, density,
        s=marker_size ** 2,
        c=color,
        alpha=alpha,
        edgecolors='none',
        label=f'Локальная плотность (окно: {window_label})',
        zorder=3
    )
    
    # Определяем, нужен ли логарифмический масштаб (до установки масштаба)
    x_min = x[0] if len(x) > 0 else 1
    x_max = x[-1] if len(x) > 0 else 1
    use_log_x = force_log_x or (x_min > 0 and x_max / x_min > 100)
    
    # Сохраняем номиналы для подписей (до изменения масштаба)
    unique_nominals = sorted(set(source_nominals)) if source_nominals else []
    
    # Вертикальные линии для исходных номиналов
    if source_nominals is not None and len(source_nominals) > 0:
        # Рисуем линии (без подписей)
        for nominal in unique_nominals:
            ax.axvline(
                x=nominal,
                color='red',
                linestyle='--',
                linewidth=0.8,
                alpha=0.5,
                zorder=2
            )
        
        # Легенда
        ax.plot(
            [], [],
            color='red',
            linestyle='--',
            linewidth=0.8,
            label=f'Исходные номиналы ({len(unique_nominals)} шт.)'
        )
    
    # Устанавливаем логарифмический масштаб ДО подписей
    if use_log_x:
        ax.set_xscale('log')
        ax.set_xlabel(f"{xlabel} (логарифмическая шкала)", fontsize=11)
    else:
        ax.set_xlabel(xlabel, fontsize=11)
    
    # Получаем пределы после установки масштаба
    x_lim = ax.get_xlim()
    y_lim = ax.get_ylim()
    y_range = y_lim[1] - y_lim[0] if y_lim[1] - y_lim[0] > 0 else 1
    
    # Подписи номиналов (после установки масштаба)
    if label_nominals and unique_nominals:
        labeled_nominals = []
        
        if use_log_x:
            # В логарифмическом масштабе — по разнице логарифмов
            min_log_dist = label_min_distance
            prev_log = None
            for nom in unique_nominals:
                if nom <= 0:
                    continue
                current_log = np.log10(nom)
                if prev_log is None or current_log - prev_log >= min_log_dist:
                    labeled_nominals.append(nom)
                    prev_log = current_log
        else:
            # В линейном масштабе — по абсолютному расстоянию в долях от диапазона
            total_range = x_lim[1] - x_lim[0] if x_lim[1] > x_lim[0] else 1
            min_abs_dist = label_min_distance * total_range
            prev_val = None
            for nom in unique_nominals:
                if nom < x_lim[0] or nom > x_lim[1]:
                    continue
                if prev_val is None or nom - prev_val >= min_abs_dist:
                    labeled_nominals.append(nom)
                    prev_val = nom
        
        # Рисуем подписи
        for idx, nominal in enumerate(labeled_nominals):
            # Позиция по Y: чуть выше верхней границы графика (offset от верхней границы)
            y_pos = y_lim[1] + y_range * label_y_offset
            
            # Форматируем число
            if nominal >= 1000:
                label_text = f"{nominal/1000:.1f}k"
            elif nominal >= 1:
                label_text = f"{nominal:.3f}"
            else:
                label_text = f"{nominal:.3f}"
            
            ax.text(
                nominal,
                y_pos,
                label_text,
                fontsize=label_fontsize,
                color='red',
                ha='center',
                va='bottom',
                rotation=label_rotation,
                bbox=dict(
                    boxstyle='round,pad=0.2',
                    facecolor='white',
                    edgecolor='red',
                    alpha=0.7,
                    linewidth=0.5
                ),
                zorder=4
            )
    
    if title is None:
        title = "Плотность значений"
    ax.set_title(title, fontsize=13, fontweight='bold')
    
    # Логарифмическая шкала по Y
    use_log_y = force_log_y or (
        len(density) > 1 and density.min() > 0 and density.max() / max(density.min(), 1) > 50
    )
    if use_log_y:
        ax.set_yscale('log')
        ax.set_ylabel(f"{ylabel} (логарифмическая шкала)", fontsize=11)
    else:
        ax.set_ylabel(ylabel, fontsize=11)
    
    # Сетка
    if grid:
        ax.grid(
            True,
            which='major',
            linestyle='-',
            linewidth=0.6,
            alpha=grid_alpha,
            color='gray'
        )
        if grid_which in ("minor", "both"):
            ax.grid(
                True,
                which='minor',
                linestyle=':',
                linewidth=0.4,
                alpha=grid_alpha * 0.8,
                color='gray'
            )
        ax.minorticks_on()
    
    ax.legend(loc='upper right', fontsize=9)
    
    fig.tight_layout()
    
    if save_path:
        save_path = Path(save_path)
        if save_path.is_dir():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = save_path / f"density_plot_{timestamp}.png"
        else:
            save_path.parent.mkdir(parents=True, exist_ok=True)
        
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] plot_density: сохранено в {save_path}")
    
    if show_plot:
        plt.show()
    
    return fig