"""Эмулятор командной оболочки UNIX-подобной ОС.

Этап 1: минимальный REPL-прототип с командами-заглушками.
"""

import getpass
import os
import socket
import sys
from typing import Callable, Dict, List

PROMPT_TILDE = "~"
HOST_UNKNOWN = "unknown-host"
HOME_ENV = "HOME"
EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def get_username() -> str:
    """Вернуть имя текущего пользователя."""
    try:
        return getpass.getuser()
    except Exception:
        return "user"


def get_hostname() -> str:
    """Вернуть имя хоста текущей машины."""
    try:
        return socket.gethostname() or HOST_UNKNOWN
    except Exception:
        return HOST_UNKNOWN


def get_current_dir() -> str:
    """Вернуть текущую директорию, заменив HOME на '~'."""
    try:
        cwd = os.getcwd()
    except OSError:
        return PROMPT_TILDE

    home = os.environ.get(HOME_ENV, "")
    if home and cwd.startswith(home):
        suffix = cwd[len(home):]
        return PROMPT_TILDE + suffix
    return cwd


def build_prompt() -> str:
    """Сформировать приглашение вида user@host:cwd$."""
    user = get_username()
    host = get_hostname()
    cwd = get_current_dir()
    return f"{user}@{host}:{cwd}$ "


def parse_input(raw: str) -> tuple:
    """Разбить ввод на команду и список аргументов по пробелам.

    Возвращает кортеж (command, args). При пустом вводе command=None.
    """
    tokens = raw.strip().split()
    if not tokens:
        return None, []
    return tokens[0], tokens[1:]


def cmd_ls(args: List[str]) -> int:
    """Заглушка команды ls: выводит имя и аргументы."""
    print("ls: заглушка")
    if args:
        print("  аргументы: " + " ".join(args))
    else:
        print("  аргументы: (нет)")
    return EXIT_SUCCESS


def cmd_cd(args: List[str]) -> int:
    """Заглушка команды cd: выводит имя и аргументы."""
    print("cd: заглушка")
    if args:
        print("  аргументы: " + " ".join(args))
    else:
        print("  аргументы: (нет)")
    return EXIT_SUCCESS


def cmd_exit(args: List[str]) -> int:
    """Команда выхода из эмулятора."""
    print("exit: завершение работы")
    return EXIT_FAILURE


def cmd_help(args: List[str]) -> int:
    """Показать список доступных команд."""
    print("Доступные команды: ls, cd, help, exit")
    return EXIT_SUCCESS


def build_commands() -> Dict[str, Callable[[List[str]], int]]:
    """Собрать таблицу поддерживаемых команд."""
    return {
        "ls": cmd_ls,
        "cd": cmd_cd,
        "help": cmd_help,
        "exit": cmd_exit,
    }


def dispatch(command: str, args: List[str]) -> int:
    """Найти и выполнить команду по имени.

    Возвращает код статуса: EXIT_SUCCESS или EXIT_FAILURE.
    EXIT_FAILURE для exit означает завершение цикла.
    """
    commands = build_commands()
    handler = commands.get(command)

    if handler is None:
        print(f"{command}: команда не найдена", file=sys.stderr)
        return EXIT_SUCCESS

    if command == "cd" and len(args) > 1:
        print("cd: слишком много аргументов", file=sys.stderr)
        return EXIT_SUCCESS

    return handler(args)


def run_repl() -> int:
    """Запустить основной цикл REPL."""
    print("Эмулятор оболочки (этап 1). Введите 'help' или 'exit'.")

    while True:
        try:
            raw = input(build_prompt())
        except EOFError:
            print()
            return EXIT_SUCCESS
        except KeyboardInterrupt:
            print()
            continue

        command, args = parse_input(raw)
        if command is None:
            continue

        status = dispatch(command, args)
        if command == "exit":
            return EXIT_SUCCESS if status == EXIT_FAILURE else status


def main() -> int:
    """Точка входа приложения."""
    return run_repl()


if __name__ == "__main__":
    sys.exit(main())