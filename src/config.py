"""Разбор параметров командной строки для эмулятора оболочки.

Поддерживаются параметры:
    --vfs PATH     — путь к физическому расположению VFS;
    --script PATH  — путь к стартовому скрипту команд эмулятора.
"""

import argparse
import os
from dataclasses import dataclass, field
from typing import List, Optional

PLACEHOLDER = "(не задан)"
ARGS_LIMIT = 7


@dataclass
class Config:
    """Конфигурация эмулятора, собранная из CLI-параметров.

    :param vfs_path: абсолютный путь к VFS или None.
    :param script_path: абсолютный путь к стартовому скрипту или None.
    :param raw_argv: исходные аргументы командной строки (для отладки).
    """

    vfs_path: Optional[str] = None
    script_path: Optional[str] = None
    raw_argv: List[str] = field(default_factory=list)


def build_parser() -> argparse.ArgumentParser:
    """Создать парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="emulator",
        description="Эмулятор оболочки UNIX-подобной ОС.",
    )
    parser.add_argument(
        "--vfs",
        metavar="PATH",
        default=None,
        help="путь к физическому расположению VFS",
    )
    parser.add_argument(
        "--script",
        metavar="PATH",
        default=None,
        help="путь к стартовому скрипту команд эмулятора",
    )
    return parser


def normalize_path(path: Optional[str]) -> Optional[str]:
    """Привести путь к абсолютному виду.

    Возвращает None, если путь не задан.
    """
    if path is None:
        return None
    return os.path.abspath(path)


def parse_args(argv: Optional[List[str]] = None) -> Config:
    """Разобрать argv и вернуть заполненный Config.

    Если argv не передан, используется sys.argv[1:].
    """
    parser = build_parser()
    namespace = parser.parse_args(argv)
    raw = list(argv) if argv is not None else []
    return Config(
        vfs_path=normalize_path(namespace.vfs),
        script_path=normalize_path(namespace.script),
        raw_argv=raw,
    )


def validate_config(config: Config) -> List[str]:
    """Проверить конфигурацию и вернуть список сообщений об ошибках."""
    errors: List[str] = []

    if config.vfs_path:
        if not os.path.exists(config.vfs_path):
            errors.append(f"VFS не найдена: {config.vfs_path}")
        elif not os.path.isdir(config.vfs_path):
            errors.append(f"VFS не директория: {config.vfs_path}")

    if config.script_path and not os.path.isfile(config.script_path):
        errors.append(f"Скрипт не найден: {config.script_path}")

    return errors


def format_debug(config: Config) -> str:
    """Сформировать отладочный вывод всех параметров.

    Используется при запуске эмулятора в этапе 2.
    """
    vfs = config.vfs_path or PLACEHOLDER
    script = config.script_path or PLACEHOLDER
    argv = config.raw_argv or []
    lines = [
        "[debug] Параметры запуска эмулятора:",
        f"[debug]   vfs_path    = {vfs}",
        f"[debug]   script_path = {script}",
        f"[debug]   argv        = {argv}",
    ]
    return "\n".join(lines)