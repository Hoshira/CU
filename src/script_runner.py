"""Исполнение стартового скрипта команд эмулятора.

Скрипт — обычный текстовый файл, по одной команде на строку.
Пустые строки и строки, начинающиеся с '#', игнорируются.
Ошибочные команды не прерывают выполнение: строка пропускается,
в stderr выводится сообщение об ошибке.
"""

import sys
from typing import Callable, List, Tuple

from .config import Config

COMMENT_PREFIX = "#"
PROMPT_TEMPLATE = "{cwd}$ "


class ScriptError(Exception):
    """Ошибка при чтении или исполнении стартового скрипта."""


def read_script_lines(path: str) -> List[str]:
    """Прочитать строки скрипта, отбросив пустые и комментарии.

    :raises ScriptError: если файл нельзя открыть или прочитать.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw_lines = handle.readlines()
    except OSError as exc:
        raise ScriptError(f"не удалось прочитать скрипт: {exc}") from exc

    lines: List[str] = []
    for raw in raw_lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith(COMMENT_PREFIX):
            continue
        lines.append(stripped)
    return lines


def run_script(
    path: str,
    dispatch: Callable[[str, List[str]], int],
    parse_input: Callable[[str], Tuple[str, List[str]]],
    echo: bool = True,
) -> int:
    """Выполнить скрипт, имитируя диалог с пользователем.

    :param path: путь к файлу скрипта.
    :param dispatch: функция выполнения команды (command, args) -> int.
    :param parse_input: функция разбора строки в (command, args).
    :param echo: печатать ли ввод команд (эмуляция диалога).
    :return: количество успешно выполненных команд.
    :raises ScriptError: если файл скрипта недоступен.
    """
    lines = read_script_lines(path)
    success_count = 0

    for line in lines:
        if echo:
            print(f"> {line}")
        command, args = parse_input(line)
        if command is None:
            continue
        try:
            dispatch(command, args)
        except Exception as exc:
            print(
                f"[script] ошибка при выполнении '{line}': {exc}",
                file=sys.stderr,
            )
            continue
        success_count += 1

    return success_count


def run_script_from_config(
    config: Config,
    dispatch: Callable[[str, List[str]], int],
    parse_input: Callable[[str], Tuple[str, List[str]]],
) -> int:
    """Выполнить скрипт из конфигурации, если он задан.

    Возвращает число успешно выполненных команд (0, если скрипта нет).
    """
    if not config.script_path:
        return 0
    return run_script(config.script_path, dispatch, parse_input)