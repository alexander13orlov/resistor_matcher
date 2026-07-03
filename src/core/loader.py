# src/core/loader.py
# Python 3.11+
# Загрузка данных из Excel

import pandas as pd
import logging
from typing import List, Optional, Union
from pathlib import Path

from .models import Resistor

logger = logging.getLogger(__name__)


def load_resistors_from_excel(
    filepath: Union[str, Path],
    sheet_name: Union[int, str] = 0,
    type_column: str = "Тип",
    value_column: str = "Номинал",
    tolerance_column: str = "Точность",
    quantity_column: str = "Остаток на складах",
    name_column: str = "Наименование",
    skip_zero_quantity: bool = True,
    max_repeats_per_nominal: int = 4,
) -> List[Resistor]:
    """
    Загрузка списка резисторов из Excel-файла.

    Args:
        filepath: Путь к Excel-файлу
        sheet_name: Имя или индекс листа
        type_column: Колонка с типом резистора
        value_column: Колонка с номиналом
        tolerance_column: Колонка с точностью (в долях, 0.01 = 1%)
        quantity_column: Колонка с остатком на складе
        name_column: Колонка с наименованием
        skip_zero_quantity: Пропускать строки с нулевым остатком
        max_repeats_per_nominal: Максимальное количество повторений номинала

    Returns:
        List[Resistor]: Список резисторов
    """
    logger.info(f"Загрузка данных из {filepath}")

    if not Path(filepath).exists():
        raise FileNotFoundError(f"Файл не найден: {filepath}")

    df = pd.read_excel(filepath, sheet_name=sheet_name, engine='openpyxl')
    df.columns = df.columns.str.strip()

    required = [type_column, value_column, tolerance_column, quantity_column, name_column]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Отсутствует колонка: {col}")

    resistors: List[Resistor] = []
    skipped_zero = 0
    skipped_missing = 0

    for _, row in df.iterrows():
        try:
            type_name = str(row[type_column]).strip()
            nominal = float(row[value_column])
            tolerance = float(row[tolerance_column])
            quantity_raw = row[quantity_column]
            name = str(row[name_column]).strip()

            if pd.isna(quantity_raw):
                skipped_missing += 1
                continue

            quantity = int(quantity_raw)
            if quantity <= 0:
                if skip_zero_quantity:
                    skipped_zero += 1
                    continue
                else:
                    quantity = 0

            if nominal <= 0:
                continue

            # Ограничиваем количество экземпляров
            effective_quantity = min(quantity, max_repeats_per_nominal)
            for _ in range(effective_quantity):
                resistors.append(Resistor(
                    nominal=nominal,
                    tolerance=tolerance,
                    stock=quantity,
                    name=name,
                    type_name=type_name
                ))

        except (ValueError, TypeError) as e:
            logger.warning(f"Пропуск строки: {row.to_dict()} - ошибка: {e}")

    logger.info(f"Загружено {len(resistors)} резисторов с остатком > 0")
    if skipped_zero > 0:
        logger.info(f"Пропущено строк с нулевым остатком: {skipped_zero}")
    if skipped_missing > 0:
        logger.info(f"Пропущено строк с отсутствующим остатком: {skipped_missing}")

    return resistors


def load_resistor_values_from_excel(
    filepath: Union[str, Path],
    sheet_name: Union[int, str] = 0,
    value_column: str = "Номинал",
    quantity_column: str = "Остаток на складах",
    max_repeats_per_nominal: int = 4,
) -> List[float]:
    """
    Загрузка только значений номиналов из Excel (для обратной совместимости).

    Returns:
        List[float]: Список номиналов (с повторениями)
    """
    resistors = load_resistors_from_excel(
        filepath=filepath,
        sheet_name=sheet_name,
        value_column=value_column,
        quantity_column=quantity_column,
        max_repeats_per_nominal=max_repeats_per_nominal,
    )
    return [r.nominal for r in resistors]