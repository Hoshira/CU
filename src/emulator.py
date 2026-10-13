"""Эмулятор командной оболочки UNIX-подобной ОС.

Этап 2: конфигурация через CLI-параметры и стартовый скрипт.
"""

import getpass
import os
import socket
import sys
from typing import Callable, Dict, List, Optional

from .config import Config, format_debug, parse_args, validate_config
from .script_runner import ScriptError, run_script_from_config

PROMPT_TILDE = "~"
HOST_UNKNOWN = "unknown-host"
HOME_ENV = "HOME"
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_CONFIG_ERROR = 2
MAX_CD_ARGS = 1

COMMANDS: Dict[str, str] = {
    "ls": "ls: заглушка",
    "cd": "cd: заглушка",
    "pwd": "pwd: заглушка",
    "help": "Список команд: ls, cd, pwd, help, exit",
    "exit": "exit: завершение работы",
}


def get_username() -> str:
    """Вернуть имя текущего пользователя."""
    try:
        return getpass.getuser()
    except Exception:  # noqa: BLE001
        return "user"


def get_hostname() -> str:
    """Вернуть имя хоста текущей машины."""
    try:
        return socket.gethostname() or HOST_UNKNOWN
    except Exception:  # noqa: BLE001
        return HOST_UNKNOWN


def get_current_dir() -> str:
    """Вернуть текущую директорию, заменив HOME на '~'."""
    try:
        cwd = os.getcwd()
    except OSError:
        return PROMPT_TILDE
    home = os.environ.get(HOME_ENV, "")
    if home and cwd.startswith(home):
        return PROMPT_TILDE + cwd[len(home):]
    return cwd


def build_prompt() -> str:
    """Сформировать приглашение вида user@host:cwd$."""
    user = get_username()
    host = get_hostname()
    cwd = get_current_dir()
    return f"{user}@{host}:{cwd}$ "


def parse_input(raw: str) -> tuple:
    """Разбить ввод на команду и список аргументов по пробелам."""
    tokens = raw.strip().split()
    if not tokens:
        return None, []
    return tokens[0], tokens[1:]


def _print_stub(name: str, args: List[str]) -> int:
    """Напечатать информацию о заглушке команды."""
    print(COMMANDS.get(name, f"{name}: заглушка"))
    joined = " ".join(args) if args else "(нет)"
    print(f"  аргументы: {joined}")
    return EXIT_SUCCESS


def cmd_ls(args: List[str]) -> int:
    """Заглушка команды ls: выводит имя и аргументы."""
    return _print_stub("ls", args)


def cmd_cd(args: List[str]) -> int:
    """Заглушка команды cd: выводит имя и аргументы."""
    return _print_stub("cd", args)


def cmd_pwd(args: List[str]) -> int:
    """Заглушка команды pwd: печатает текущую директорию."""
    print(get_current_dir())
    return EXIT_SUCCESS


def cmd_help(args: List[str]) -> int:
    """Показать список доступных команд."""
    print(COMMANDS["help"])
    return EXIT_SUCCESS


def cmd_exit(args: List[str]) -> int:
    """Команда выхода из эмулятора."""
    print(COMMANDS["exit"])
    return EXIT_FAILURE


def build_commands() -> Dict[str, Callable[[List[str]], int]]:
    """Собрать таблицу поддерживаемых команд."""
    return {
        "ls": cmd_ls,
        "cd": cmd_cd,
        "pwd": cmd_pwd,
        "help": cmd_help,
        "exit": cmd_exit,
    }


def dispatch(command: str, args: List[str]) -> int:
    """Найти и выполнить команду по имени."""
    handler = build_commands().get(command)
    if handler is None:
        print(f"{command}: команда не найдена", file=sys.stderr)
        return EXIT_SUCCESS
    if command == "cd" and len(args) > MAX_CD_ARGS:
        print("cd: слишком много аргументов", file=sys.stderr)
        return EXIT_SUCCESS
    return handler(args)


def _read_line() -> Optional[str]:
    """Прочитать строку из stdin, обработав EOF и Ctrl+C.

    Возвращает None, если ввод завершён (EOF).
    Возвращает '' при Ctrl+C.
    """
    try:
        return input(build_prompt())
    except EOFError:
        print()
        return None
    except KeyboardInterrupt:
        print()
        return ""


def run_repl() -> int:
    """Запустить основной цикл REPL."""
    print("Эмулятор оболочки (этап 2). Введите 'help' или 'exit'.")
    while True:
        raw = _read_line()
        if raw is None:
            return EXIT_SUCCESS
        command, args = parse_input(raw)
        if command is None:
            continue
        status = dispatch(command, args)
        if command == "exit":
            return EXIT_SUCCESS if status == EXIT_FAILURE else status


def print_config_errors(errors: List[str]) -> None:
    """Напечатать ошибки конфигурации в stderr."""
    for message in errors:
        print(f"[config] {message}", file=sys.stderr)


def prepare_config(argv: Optional[List[str]] = None) -> Config:
    """Разобрать argv, проверить и напечатать отладку.

    Возвращает Config либо завершает процесс с кодом ошибки.
    """
    config = parse_args(argv)
    print(format_debug(config))
    errors = validate_config(config)
    if errors:
        print_config_errors(errors)
        sys.exit(EXIT_CONFIG_ERROR)
    return config


def run_with_script(config: Config) -> int:
    """Выполнить стартовый скрипт и вернуть код возврата."""
    try:
        run_script_from_config(config, dispatch, parse_input)
    except ScriptError as exc:
        print(f"[script] {exc}", file=sys.stderr)
        return EXIT_FAILURE
    return EXIT_SUCCESS


def main(argv: Optional[List[str]] = None) -> int:
    """Точка входа приложения."""
    config = prepare_config(argv)
    if config.script_path:
        return run_with_script(config)
    return run_repl()


if __name__ == "__main__":
    sys.exit(main())