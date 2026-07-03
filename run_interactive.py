# run_interactive.py
# Интерактивная обёртка для консольного приложения
# Python 3.11+

import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.cli.commands.combined_search import run_combined_search


def print_header() -> None:
    """Вывод заголовка"""
    print("=" * 80)
    print("RESISTOR MATCHER - интерактивный режим")
    print("=" * 80)
    print("Команды:")
    print("  search --nominal 89.341 --n-results 5 --size 1,2,3,4")
    print("  search -n 89.341 -nr 5 -s 1,2")
    print("  s 89.341 5 1,2")
    print("  help, h")
    print("  exit, quit, q")
    print("=" * 80)


def parse_command(line: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Парсинг команды с поддержкой сокращений.
    
    Returns:
        Tuple[Optional[str], Optional[Dict]]: (команда, аргументы)
    """
    line = line.strip()
    if not line:
        return None, None

    parts = line.split()
    cmd = parts[0].lower()

    # Команды выхода
    if cmd in ("exit", "quit", "q"):
        return "exit", None

    # Справка
    if cmd in ("help", "h"):
        return "help", None

    # Сокращённый формат: s 89.341 5 1,2
    if cmd == "s" and len(parts) >= 2:
        try:
            nominal = float(parts[1])
            n_results = int(parts[2]) if len(parts) >= 3 else 5
            size = parts[3] if len(parts) >= 4 else "1,2,3,4"
            return "search", {"nominal": nominal, "n_results": n_results, "size": size}
        except ValueError:
            return None, None

    # Полный формат: search --nominal 89.341 --n-results 5 --size 1,2
    if cmd == "search":
        args: Dict[str, Any] = {}
        i = 1
        while i < len(parts):
            arg = parts[i]
            if arg in ("--nominal", "-n"):
                if i + 1 < len(parts):
                    try:
                        args["nominal"] = float(parts[i + 1])
                        i += 2
                        continue
                    except ValueError:
                        pass
            elif arg in ("--n-results", "-nr"):
                if i + 1 < len(parts):
                    try:
                        args["n_results"] = int(parts[i + 1])
                        i += 2
                        continue
                    except ValueError:
                        pass
            elif arg in ("--size", "-s"):
                if i + 1 < len(parts):
                    args["size"] = parts[i + 1]
                    i += 2
                    continue
            i += 1

        if "nominal" in args:
            if "size" not in args:
                args["size"] = "1,2,3,4"
            return "search", args

    return None, None


def main() -> None:
    """Интерактивный режим"""
    print_header()

    while True:
        try:
            line = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            print("\nВыход...")
            break

        cmd, args = parse_command(line)

        if cmd == "exit":
            print("Выход...")
            break

        if cmd == "help":
            print_header()
            continue

        if cmd == "search" and args is not None:
            # Извлекаем значения с проверкой типа
            nominal_raw = args.get("nominal")
            n_results_raw = args.get("n_results", 5)
            size = args.get("size", "1,2,3,4")

            # Проверяем, что nominal — это float
            if not isinstance(nominal_raw, (int, float)):
                print("Ошибка: номинал должен быть числом")
                continue

            nominal = float(nominal_raw)
            n_results = int(n_results_raw) if isinstance(n_results_raw, (int, float)) else 5

            print("-" * 80)
            print(f"Поиск для {nominal} Ом, {n_results} результатов, размеры: {size}")
            print("-" * 80)

            start_time = time.time()

            try:
                result = run_combined_search(nominal, n_results, size)
                
                elapsed = time.time() - start_time
                print(f"\nВремя выполнения: {elapsed:.2f} сек")

                if result is not None and result.get("combined_search"):
                    print(f"Всего ближайших комбинаций: {len(result['combined_search'])}")
                else:
                    print("Результатов не найдено")
            except Exception as e:
                print(f"Ошибка: {e}")

            continue

        if line:
            print(f"Неизвестная команда: {line}")

    print("Завершено.")


if __name__ == "__main__":
    main()