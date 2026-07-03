import os
import argparse

# Списки для исключения (можно расширять)
DEFAULT_EXCLUDE_DIRS = {
    '__pycache__', '.pytest_cache', '.mypy_cache', '.hypothesis',
    '.tox', '.venv', 'venv', 'env', '.env', 'env.bak',
    'build', 'dist', '*.egg-info', '.eggs',
    '.git', '.svn', '.hg', '.idea', '.vscode', '.vs',
    'node_modules', 'bower_components',
    '.cache', '.coverage', '.nox', '.scannerwork'
}

DEFAULT_EXCLUDE_FILES = {
    '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll',
    '*.egg', '*.whl',
    '.coverage', 'coverage.xml', '*.cover', '.hypothesis',
    '*.log', '*.sqlite', '*.db', '*.cache',
    '.python-version', '.DS_Store', 'thumbs.db',
    'desktop.ini', '.localized'
}

def should_exclude(name, exclude_patterns):
    """Проверяет, нужно ли исключить файл/папку по паттерну"""
    for pattern in exclude_patterns:
        if pattern.startswith('*'):
            # Паттерн типа *.ext
            if name.endswith(pattern[1:]):
                return True
        elif name == pattern:
            # Точное совпадение
            return True
    return False

def print_tree(root_dir, prefix='', is_last=True, 
               exclude_dirs=None, exclude_files=None,
               show_hidden=False, level=0):
    """Рекурсивно отрисовывает дерево директорий с ASCII-графикой"""
    
    if exclude_dirs is None:
        exclude_dirs = set()
    if exclude_files is None:
        exclude_files = set()
    
    # Получаем базовое имя для корневой директории
    if level == 0:
        basename = os.path.basename(os.path.abspath(root_dir))
    else:
        basename = os.path.basename(root_dir or '.')
    
    # Пропускаем скрытые файлы/папки если не включен показ
    if not show_hidden and basename.startswith('.') and level > 0:
        return
    
    # Текущий элемент (используем ASCII-символы)
    connector = '\\-- ' if is_last else '|-- '
    print(prefix + connector + basename)

    # Обновление префикса для следующих уровней
    if not is_last:
        new_prefix = prefix + '|   '
    else:
        new_prefix = prefix + '    '

    try:
        items = []
        for item in os.listdir(root_dir):
            item_path = os.path.join(root_dir, item)
            
            # Пропускаем скрытые файлы если не включен показ
            if not show_hidden and item.startswith('.') and level > 0:
                continue
            
            # Проверяем исключения для директорий
            if os.path.isdir(item_path):
                if should_exclude(item, exclude_dirs):
                    continue
            
            # Проверяем исключения для файлов
            elif should_exclude(item, exclude_files):
                continue
            
            items.append(item)
        
        # Сортировка: сначала директории, потом файлы
        items.sort(key=lambda x: (
            not os.path.isdir(os.path.join(root_dir, x)), 
            x.lower()
        ))
        
        for i, item in enumerate(items):
            item_path = os.path.join(root_dir, item)
            is_last_item = (i == len(items) - 1)
            
            if os.path.isdir(item_path):
                print_tree(
                    item_path, 
                    new_prefix, 
                    is_last_item, 
                    exclude_dirs, 
                    exclude_files,
                    show_hidden,
                    level + 1
                )
            else:
                connector = '\\-- ' if is_last_item else '|-- '
                print(new_prefix + connector + item)
                
    except PermissionError:
        print(new_prefix + '\\-- [Permission Denied]')
    except OSError as e:
        print(new_prefix + f'\\-- [Error: {e}]')

def main():
    parser = argparse.ArgumentParser(
        description='Отображение дерева директорий Python-проекта',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры использования:
  python project_tree.py                    # Текущая директория
  python project_tree.py /path/to/project   # Указанная директория
  python project_tree.py -a                 # Показать скрытые файлы
  python project_tree.py --add-exclude-dir temp --add-exclude-file *.tmp
        '''
    )
    
    parser.add_argument(
        'root_dir', 
        nargs='?', 
        default='.', 
        help='Корневая директория проекта (по умолчанию: текущая)'
    )
    
    parser.add_argument(
        '-a', '--all',
        action='store_true',
        help='Показать скрытые файлы и папки'
    )
    
    parser.add_argument(
        '--no-default-exclude',
        action='store_true',
        help='Не использовать исключения по умолчанию'
    )
    
    parser.add_argument(
        '--add-exclude-dir',
        action='append',
        dest='additional_exclude_dirs',
        help='Дополнительные директории для исключения'
    )
    
    parser.add_argument(
        '--add-exclude-file', 
        action='append',
        dest='additional_exclude_files',
        help='Дополнительные файлы для исключения'
    )
    
    args = parser.parse_args()

    # Настройка исключений
    exclude_dirs = set()
    exclude_files = set()
    
    if not args.no_default_exclude:
        exclude_dirs.update(DEFAULT_EXCLUDE_DIRS)
        exclude_files.update(DEFAULT_EXCLUDE_FILES)
    
    if args.additional_exclude_dirs:
        exclude_dirs.update(args.additional_exclude_dirs)
    
    if args.additional_exclude_files:
        exclude_files.update(args.additional_exclude_files)

    print(f"Структура проекта: {os.path.abspath(args.root_dir)}")
    print("(исключены системные файлы и временные данные)")
    print("=" * 50)
    
    print_tree(
        args.root_dir,
        exclude_dirs=exclude_dirs,
        exclude_files=exclude_files,
        show_hidden=args.all,
        level=0
    )

if __name__ == '__main__':
    main()