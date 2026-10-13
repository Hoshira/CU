"""Эмулятор командной оболочки UNIX-подобной ОС.

Этап 3: подключена виртуальная файловая система (VFS).
"""

import getpass
import os
import socket
import sys
from typing import Callable, Dict, List, Optional, Tuple

from .config import Config, format_debug, parse_args, validate_config
from .script_runner import ScriptError, run_script_from_config
from .vfs import Vfs, VfsError, load_tree

PROMPT_TILDE = "~"
HOST_UNKNOWN = "unknown-host"
HOME_ENV = "HOME"
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_CONFIG_ERROR = 2
MAX_CD_ARGS = 1

HELP_TEXT = "Список команд: ls, cd, pwd, help, exit"
EXIT_TEXT = "exit: завершение работы"


class ShellContext:
    """Состояние текущей сессии эмулятора.

    :param vfs: виртуальная файловая система или None.
    """

    def __init__(self, vfs: Optional[Vfs] = None) -> None:
        self.vfs = vfs

    def has_vfs(self) -> bool:
        """Есть ли активная VFS в этой сессии."""
        return self.vfs is not None


CONTEXT = ShellContext()


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


def _host_cwd() -> str:
    """Текущая директория реальной ОС с заменой HOME на '~'."""
    try:
        cwd = os.getcwd()
    except OSError:
        return PROMPT_TILDE
    home = os.environ.get(HOME_ENV, "")
    if home and cwd.startswith(home):
        return PROMPT_TILDE + cwd[len(home):]
    return cwd


def virtual_cwd() -> str:
    """Текущая директория VFS или реальная, если VFS не задана."""
    if CONTEXT.has_vfs():
        return CONTEXT.vfs.path_str()
    return _host_cwd()


def build_prompt() -> str:
    """Сформировать приглашение вида user@host:cwd$."""
    user = get_username()
    host = get_hostname()
    return f"{user}@{host}:{virtual_cwd()}$ "


def parse_input(raw: str) -> Tuple[Optional[str], List[str]]:
    """Разбить ввод на команду и список аргументов по пробелам."""
    tokens = raw.strip().split()
    if not tokens:
        return None, []
    return tokens[0], tokens[1:]


def _require_vfs() -> Optional[Vfs]:
    """Вернуть VFS или напечатать ошибку и вернуть None."""
    if not CONTEXT.has_vfs():
        print("команда недоступна: VFS не задана", file=sys.stderr)
        return None
    return CONTEXT.vfs


def cmd_ls(args: List[str]) -> int:
    """Показать содержимое текущей директории VFS."""
    vfs = _require_vfs()
    if vfs is None:
        return EXIT_SUCCESS
    try:
        items = vfs.listdir()
    except VfsError as exc:
        print(f"ls: {exc}", file=sys.stderr)
        return EXIT_SUCCESS

    if not items:
        return EXIT_SUCCESS
    for name, is_dir in items:
        suffix = "/" if is_dir else ""
        print(f"{name}{suffix}")
    return EXIT_SUCCESS


def cmd_cd(args: List[str]) -> int:
    """Сменить текущую директорию VFS."""
    vfs = _require_vfs()
    if vfs is None:
        return EXIT_SUCCESS
    if len(args) > MAX_CD_ARGS:
        print("cd: слишком много аргументов", file=sys.stderr)
        return EXIT_SUCCESS

    target = args[0] if args else "/"
    try:
        vfs.change_dir(target)
    except VfsError as exc:
        print(f"cd: {exc}", file=sys.stderr)
    return EXIT_SUCCESS


def cmd_pwd(args: List[str]) -> int:
    """Показать текущую директорию VFS."""
    vfs = _require_vfs()
    if vfs is None:
        return EXIT_SUCCESS
    print(vfs.path_str())
    return EXIT_SUCCESS


def cmd_help(args: List[str]) -> int:
    """Показать список доступных команд."""
    print(HELP_TEXT)
    return EXIT_SUCCESS


def cmd_exit(args: List[str]) -> int:
    """Команда выхода из эмулятора."""
    print(EXIT_TEXT)
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
    return handler(args)


def _read_line() -> Optional[str]:
    """Прочитать строку, обработав EOF и Ctrl+C."""
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
    print("Эмулятор оболочки (этап 3). Введите 'help' или 'exit'.")
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


def load_vfs(config: Config) -> Optional[Vfs]:
    """Загрузить VFS, если путь задан.

    Возвращает Vfs или None (если путь не задан или при ошибке).
    """
    if not config.vfs_path:
        return None
    try:
        tree = load_tree(config.vfs_path)
    except VfsError as exc:
        print(f"[vfs] {exc}", file=sys.stderr)
        return None
    return Vfs(tree)


def prepare_config(argv: Optional[List[str]] = None) -> Config:
    """Разобрать argv, проверить и напечатать отладку."""
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
    CONTEXT.vfs = load_vfs(config)
    if config.script_path:
        return run_with_script(config)
    return run_repl()


if __name__ == "__main__":
    sys.exit(main())