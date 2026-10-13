"""Виртуальная файловая система (VFS) эмулятора оболочки.

VFS загружается в память из указанной директории на диске
и больше не обращается к реальной ФС. Все операции (навигация,
просмотр, создание узлов) выполняются над внутренним деревом.

Внутреннее представление:
    папка  — dict[str, node];
    файл   — None.
Текущая директория хранится как список имён от корня.
"""

import os
from typing import Dict, List, Optional, Tuple

ROOT_NAME = "/"
PARENT = ".."
CURRENT = "."
SEPARATOR = "/"


class VfsError(Exception):
    """Ошибка загрузки или работы с VFS."""


class Node:
    """Узел дерева VFS: папка или файл.

    :param name: имя узла (без пути).
    :param is_dir: True для папки, False для файла.
    :param children: словарь детей (для папок), иначе None.
    """

    def __init__(
        self,
        name: str,
        is_dir: bool,
        children: Optional[Dict[str, "Node"]] = None,
    ) -> None:
        self.name = name
        self.is_dir = is_dir
        self.children: Dict[str, "Node"] = children or {}

    def add(self, child: "Node") -> None:
        """Добавить дочерний узел (только для папок)."""
        if not self.is_dir:
            raise VfsError(f"{self.name} не является директорией")
        self.children[child.name] = child

    def get(self, name: str) -> Optional["Node"]:
        """Вернуть дочерний узел по имени или None."""
        return self.children.get(name)


def load_tree(path: str) -> Node:
    """Загрузить дерево VFS из директории на диске.

    :raises VfsError: если путь не существует, не является папкой
        или недоступен для чтения.
    """
    if not os.path.exists(path):
        raise VfsError(f"путь не найден: {path}")
    if not os.path.isdir(path):
        raise VfsError(f"путь не является директорией: {path}")
    try:
        return _scan_dir(path, ROOT_NAME)
    except OSError as exc:
        raise VfsError(f"не удалось прочитать VFS: {exc}") from exc


def _scan_dir(path: str, name: str) -> Node:
    """Рекурсивно просканировать директорию и вернуть узел-папку."""
    node = Node(name=name, is_dir=True)
    with os.scandir(path) as entries:
        for entry in sorted(entries, key=lambda e: e.name):
            child = _scan_entry(entry)
            node.add(child)
    return node


def _scan_entry(entry: os.DirEntry) -> Node:
    """Преобразовать запись scandir в узел VFS."""
    if entry.is_dir(follow_symlinks=False):
        return _scan_dir(entry.path, entry.name)
    return Node(name=entry.name, is_dir=False)


class Vfs:
    """Виртуальная файловая система.

    Хранит корень дерева и текущий путь (список имён от корня).
    Все операции — in-memory, реальная ФС после загрузки не трогается.
    """

    def __init__(self, root: Node) -> None:
        self.root = root
        self.cwd: List[str] = []

    def path_str(self) -> str:
        """Строковое представление текущей директории."""
        if not self.cwd:
            return ROOT_NAME
        return SEPARATOR + SEPARATOR.join(self.cwd)

    def resolve(self) -> Node:
        """Вернуть узел текущей директории."""
        node = self.root
        for part in self.cwd:
            child = node.get(part)
            if child is None or not child.is_dir:
                raise VfsError(f"нет такой директории: {part}")
            node = child
        return node

    def listdir(self) -> List[Tuple[str, bool]]:
        """Вернуть содержимое текущей директории.

        Возвращает список (имя, is_dir), отсортированный по имени.
        """
        node = self.resolve()
        items = [(c.name, c.is_dir) for c in node.children.values()]
        items.sort(key=lambda t: (not t[1], t[0]))
        return items

    def change_dir(self, target: str) -> None:
        """Сменить текущую директорию.

        Поддерживает абсолютные и относительные пути, '.', '..'.
        """
        parts = self._split_target(target)
        new_cwd = self._walk(parts)
        self.cwd = new_cwd

    def _split_target(self, target: str) -> List[str]:
        """Разобрать целевой путь на компоненты."""
        if target.startswith(SEPARATOR):
            return [p for p in target.split(SEPARATOR) if p]
        return self.cwd + [p for p in target.split(SEPARATOR) if p]

    def _walk(self, parts: List[str]) -> List[str]:
        """Пройти по компонентам пути и вернуть нормализованный cwd."""
        result: List[str] = []
        for part in parts:
            result = self._step(result, part)
        return result

    def _step(self, current: List[str], part: str) -> List[str]:
        """Один шаг по дереву: '.', '..' или обычное имя."""
        if part == CURRENT:
            return current
        if part == PARENT:
            return current[:-1] if current else []
        node = self._lookup(current, part)
        if node is None:
            raise VfsError(f"нет такого пути: {part}")
        if not node.is_dir:
            raise VfsError(f"не директория: {part}")
        return current + [part]

    def _lookup(self, current: List[str], name: str) -> Optional[Node]:
        """Найти узел по пути current + [name]."""
        node = self.root
        for part in current:
            node = node.get(part)
            if node is None:
                return None
        return node.get(name)