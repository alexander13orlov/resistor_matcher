# src/cli/main.py
# Точка входа: парсинг аргументов, выбор команды

import argparse
import sys
from typing import Optional, Dict, Any

from .commands.search import run_search
from .commands.analyze import run_analyze
from .commands.estimate import run_estimate


def create_parser() -> argparse.ArgumentParser:
    """Создание парсера аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Resistor Matcher — анализ и подбор комбинаций резисторов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
РЕЖИМЫ:
  Без параметров              — полный анализ с графиком
  --nominal N                 — поиск по номиналу
  --mode range --min X --max Y — поиск по диапазону
  --estimate                  — оценка сложности

ОПТИМИЗИРОВАННЫЙ ПОИСК (ВКЛЮЧЁН ПО УМОЛЧАНИЮ):
  --optimized, -opt           — использовать оптимизированный поиск (по умолчанию ВКЛЮЧЁН)
  --full-scan, -fs            — использовать полный перебор (ВЫКЛЮЧАЕТ оптимизированный)
  --topology 4-1,4-5,3-1      — конкретные топологии через запятую
  --structure 2+2,2+1         — структуры через запятую
  --fast-only, -fo            — только быстрые топологии (2+2, 2+1, 1+1, 1)
  --n-results, -nr N          — количество результатов на топологию (по умолчанию: 10)
  --auto-range, -ar           — автоматически отключать range-nominals для быстрых топологий

ПРИМЕРЫ:
  # Полный анализ с графиком
  python -m src.cli.main

  # Поиск по номиналу (оптимизированный поиск по умолчанию)
  python -m src.cli.main --nominal 9.4

  # Поиск по диапазону
  python -m src.cli.main --mode range --min 8.5 --max 9.5

  # Оценка сложности
  python -m src.cli.main --estimate

  # Отключить оптимизированный поиск (полный перебор)
  python -m src.cli.main --nominal 9.4 --full-scan

  # Только быстрые топологии, вся база
  python -m src.cli.main --nominal 9.4 --fast-only --auto-range

  # Конкретные топологии
  python -m src.cli.main --nominal 9.4 --topology 4-1,4-5

  # По структуре
  python -m src.cli.main --nominal 9.4 --structure 2+2
        """
    )

    # ================================================================
    # ОБЩИЕ ПАРАМЕТРЫ
    # ================================================================
    parser.add_argument(
        "file", nargs="?", default="db/resistor.xlsx",
        help="Путь к Excel-файлу (по умолчанию: db/resistor.xlsx)"
    )
    parser.add_argument(
        "--precision", "-p", type=int, default=6,
        help="Точность округления (по умолчанию: 6)"
    )
    parser.add_argument(
        "--max-repeats", "-r", type=int, default=4,
        help="Максимум экземпляров одного номинала (по умолчанию: 4)"
    )

    # ================================================================
    # РЕЖИМЫ
    # ================================================================
    parser.add_argument(
        "--estimate", action="store_true",
        help="Только оценка сложности (без полного анализа)"
    )

    # ================================================================
    # ПАРАМЕТРЫ ПОИСКА
    # ================================================================
    parser.add_argument(
        "--mode", "-m", choices=["nominal", "range"], default="nominal",
        help="Режим поиска: nominal (по номиналу) или range (по диапазону) (по умолчанию: nominal)"
    )
    parser.add_argument(
        "--nominal", "-n", type=float,
        help="Целевое сопротивление (для --mode nominal)"
    )
    parser.add_argument(
        "--min", "-min", type=float,
        help="Нижняя граница (для --mode range)"
    )
    parser.add_argument(
        "--max", "-max", type=float,
        help="Верхняя граница (для --mode range)"
    )
    parser.add_argument(
        "--eps", "-e", type=int, default=10,
        help="Окрестность в позициях (по умолчанию: 10)"
    )
    parser.add_argument(
        "--range-nominals", "-rn", type=str, default="15",
        help="Соседние номиналы: '15' или '10,5' (по умолчанию: 15). "
             "Укажите '0' для отключения фильтрации."
    )

    # ================================================================
    # ДЕТАЛИЗАЦИЯ
    # ================================================================
    parser.add_argument(
        "--details", "-d", action="store_true",
        help="Показывать полную детализацию всех значений"
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=100,
        help="Лимит строк детализации (по умолчанию: 100)"
    )

    # ================================================================
    # ГРАФИК
    # ================================================================
    parser.add_argument(
        "--graph", "-g", action="store_true",
        help="Построить график плотности (для режима поиска)"
    )
    parser.add_argument(
        "--save", "-s", type=str, default="img/",
        help="Папка для сохранения графика (по умолчанию: img/)"
    )
    parser.add_argument(
        "--no-show", action="store_true",
        help="Не показывать график (только сохранить)"
    )

    # ================================================================
    # ТОПОЛОГИИ (включение/отключение)
    # ================================================================
    group_include = parser.add_argument_group("Топологии (включение)")
    group_include.add_argument("--4", dest="inc4", action="store_true", default=True)
    group_include.add_argument("--3", dest="inc3", action="store_true", default=True)
    group_include.add_argument("--2", dest="inc2", action="store_true", default=True)
    group_include.add_argument("--1", dest="inc1", action="store_true", default=True)

    group_exclude = parser.add_argument_group("Топологии (отключение)")
    group_exclude.add_argument("--no-4", dest="inc4", action="store_false")
    group_exclude.add_argument("--no-3", dest="inc3", action="store_false")
    group_exclude.add_argument("--no-2", dest="inc2", action="store_false")
    group_exclude.add_argument("--no-1", dest="inc1", action="store_false")

    # ================================================================
    # ОПТИМИЗИРОВАННЫЙ ПОИСК
    # ================================================================
    opt_group = parser.add_argument_group("Оптимизированный поиск")
    opt_group.add_argument(
        "--optimized", "-opt", action="store_true", default=True,
        help="Использовать оптимизированный поиск (по умолчанию ВКЛЮЧЁН)"
    )
    opt_group.add_argument(
        "--full-scan", "-fs", action="store_true",
        help="Использовать полный перебор (ВЫКЛЮЧАЕТ оптимизированный поиск)"
    )
    opt_group.add_argument(
        "--topology", "-t", type=str, default=None,
        help="Топологии через запятую: '4-1,4-5,3-1'"
    )
    opt_group.add_argument(
        "--structure", "-st", type=str, default=None,
        help="Структуры через запятую: '2+2,2+1'"
    )
    opt_group.add_argument(
        "--fast-only", "-fo", action="store_true",
        help="Использовать только быстрые топологии (2+2, 2+1, 1+1, 1)"
    )
    opt_group.add_argument(
        "--n-results", "-nr", type=int, default=10,
        help="Количество результатов на топологию (по умолчанию: 10)"
    )
    opt_group.add_argument(
        "--auto-range", "-ar", action="store_true",
        help="Автоматически отключать range-nominals для быстрых топологий"
    )

    return parser


def execute_command(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    """
    Выполнение команды на основе аргументов.
    
    Returns:
        Optional[Dict]: Результат выполнения (для команд поиска/анализа),
                        None для оценки или при ошибке.
    """
    # Режим оценки
    if args.estimate:
        run_estimate(
            filepath=args.file,
            max_repeats=args.max_repeats,
            range_nominals=args.range_nominals,
            inc4=args.inc4,
            inc3=args.inc3,
            inc2=args.inc2,
            inc1=args.inc1,
        )
        return None

    # Режим поиска
    use_optimized = args.optimized and not args.full_scan

    if args.mode == "nominal" and args.nominal is not None:
        result = run_search(
            filepath=args.file,
            mode="nominal",
            nominal=args.nominal,
            eps=args.eps,
            range_nominals=args.range_nominals,
            precision=args.precision,
            max_repeats=args.max_repeats,
            inc4=args.inc4,
            inc3=args.inc3,
            inc2=args.inc2,
            inc1=args.inc1,
            show_details=args.details,
            details_limit=args.limit,
            with_graph=args.graph,
            save_graph=args.save,
            show_graph=not args.no_show,
            optimized=use_optimized,
            topologies=args.topology,
            structure=args.structure,
            fast_only=args.fast_only,
            n_results=args.n_results,
            auto_range=args.auto_range,
        )
        return result

    if args.mode == "range" and args.min is not None and args.max is not None:
        result = run_search(
            filepath=args.file,
            mode="range",
            r_min=args.min,
            r_max=args.max,
            eps=args.eps,
            range_nominals=args.range_nominals,
            precision=args.precision,
            max_repeats=args.max_repeats,
            inc4=args.inc4,
            inc3=args.inc3,
            inc2=args.inc2,
            inc1=args.inc1,
            show_details=args.details,
            details_limit=args.limit,
            with_graph=args.graph,
            save_graph=args.save,
            show_graph=not args.no_show,
            optimized=use_optimized,
            topologies=args.topology,
            structure=args.structure,
            fast_only=args.fast_only,
            n_results=args.n_results,
            auto_range=args.auto_range,
        )
        return result

    # Полный анализ (без параметров)
    run_analyze(
        filepath=args.file,
        precision=args.precision,
        max_repeats=args.max_repeats,
        inc4=args.inc4,
        inc3=args.inc3,
        inc2=args.inc2,
        inc1=args.inc1,
        save_graph=args.save,
        show_graph=not args.no_show,
        show_details=args.details,
        details_limit=args.limit,
    )
    return None


def main() -> None:
    """Точка входа CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Проверка обязательных параметров
    if args.mode == "range" and (args.min is None or args.max is None):
        parser.error("Для --mode range необходимо указать --min и --max")
    if args.mode == "nominal" and args.nominal is None:
        parser.error("Для --mode nominal необходимо указать --nominal")

    execute_command(args)


if __name__ == "__main__":
    main()