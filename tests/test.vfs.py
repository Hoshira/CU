"""Тесты виртуальной файловой системы (VFS).

Покрывают:
    - загрузку дерева из директории на диске;
    - ошибки загрузки (путь не найден, не директория);
    - навигацию (change_dir) с относительными и абсолютными путями;
    - переходы через '.' и '..';
    - просмотр содержимого (listdir);
    - строковое представление пути (path_str).

Все тесты создают VFS во временной папке через tempfile,
не трогая vfs_samples/ и data/.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import vfs  # noqa: E402


def _make(tmp: str, files) -> str:
    """Создать структуру файлов в tmp и вернуть путь корня.

    :param tmp: путь к временной директории.
    :param files: список относительных путей (например, ["d/a.txt"]).
    :return: тот же путь tmp.
    """
    for rel in files:
        full = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write("")
    return tmp


class TestLoadTree(unittest.TestCase):
    """Проверка загрузки дерева VFS из директории."""

    def test_missing_path(self):
        with self.assertRaises(vfs.VfsError):
            vfs.load_tree("C:/no/such/path/xyz")

    def test_not_a_dir(self):
        with tempfile.NamedTemporaryFile() as fp:
            with self.assertRaises(vfs.VfsError):
                vfs.load_tree(fp.name)

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = vfs.load_tree(tmp)
            self.assertTrue(root.is_dir)
            self.assertEqual(root.children, {})

    def test_root_is_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make(tmp, ["a.txt"])
            root = vfs.load_tree(tmp)
            self.assertTrue(root.is_dir)

    def test_files_and_dirs_in_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make(tmp, ["a.txt", "b.txt", "d/c.txt"])
            root = vfs.load_tree(tmp)
            self.assertIn("a.txt", root.children)
            self.assertIn("b.txt", root.children)
            self.assertIn("d", root.children)

    def test_nested_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make(tmp, ["a.txt", "d/b.txt", "d/e/c.txt"])
            root = vfs.load_tree(tmp)
            d = root.children["d"]
            self.assertTrue(d.is_dir)
            self.assertIn("b.txt", d.children)
            self.assertIn("e", d.children)
            e = d.children["e"]
            self.assertTrue(e.is_dir)
            self.assertIn("c.txt", e.children)

    def test_file_is_not_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make(tmp, ["a.txt"])
            root = vfs.load_tree(tmp)
            node = root.children["a.txt"]
            self.assertFalse(node.is_dir)


class TestVfsBasics(unittest.TestCase):
    """Базовые свойства Vfs: path_str, начальный cwd."""

    def _vfs(self):
        tmp = tempfile.mkdtemp()
        _make(tmp, ["a.txt", "d/b.txt", "d/e/c.txt"])
        return vfs.Vfs(vfs.load_tree(tmp))

    def test_initial_cwd_is_root(self):
        fs = self._vfs()
        self.assertEqual(fs.cwd, [])
        self.assertEqual(fs.path_str(), "/")

    def test_path_str_after_manual_cwd(self):
        fs = self._vfs()
        fs.cwd = ["d"]
        self.assertEqual(fs.path_str(), "/d")


class TestListdir(unittest.TestCase):
    """Проверка просмотра содержимого директорий."""

    def _vfs(self):
        tmp = tempfile.mkdtemp()
        _make(tmp, ["a.txt", "b.txt", "d/c.txt", "d/e/f.txt"])
        return vfs.Vfs(vfs.load_tree(tmp))

    def test_root_dirs_first(self):
        fs = self._vfs()
        items = fs.listdir()
        names = [name for name, _ in items]
        self.assertEqual(names, ["d", "a.txt", "b.txt"])

    def test_root_marks_dirs(self):
        fs = self._vfs()
        items = dict(fs.listdir())
        self.assertTrue(items["d"])
        self.assertFalse(items["a.txt"])

    def test_nested_listdir(self):
        fs = self._vfs()
        fs.change_dir("d")
        names = [name for name, _ in fs.listdir()]
        self.assertEqual(names, ["e", "c.txt"])

    def test_empty_dir_listdir(self):
        tmp = tempfile.mkdtemp()
        _make(tmp, ["d/.keep"])
        fs = vfs.Vfs(vfs.load_tree(tmp))
        fs.change_dir("d")
        items = fs.listdir()
        names = [name for name, _ in items]
        self.assertIn(".keep", names)


class TestChangeDirRelative(unittest.TestCase):
    """Навигация относительными путями."""

    def _vfs(self):
        tmp = tempfile.mkdtemp()
        _make(tmp, ["d/b.txt", "d/e/c.txt"])
        return vfs.Vfs(vfs.load_tree(tmp))

    def test_cd_into_child(self):
        fs = self._vfs()
        fs.change_dir("d")
        self.assertEqual(fs.path_str(), "/d")

    def test_cd_two_levels(self):
        fs = self._vfs()
        fs.change_dir("d/e")
        self.assertEqual(fs.path_str(), "/d/e")

    def test_cd_parent(self):
        fs = self._vfs()
        fs.change_dir("d/e")
        fs.change_dir("..")
        self.assertEqual(fs.path_str(), "/d")

    def test_cd_parent_from_root(self):
        fs = self._vfs()
        fs.change_dir("..")
        self.assertEqual(fs.path_str(), "/")

    def test_cd_current(self):
        fs = self._vfs()
        fs.change_dir("d")
        fs.change_dir(".")
        self.assertEqual(fs.path_str(), "/d")

    def test_cd_unknown(self):
        fs = self._vfs()
        with self.assertRaises(vfs.VfsError):
            fs.change_dir("no_such_dir")

    def test_cd_to_file_fails(self):
        tmp = tempfile.mkdtemp()
        _make(tmp, ["a.txt"])
        fs = vfs.Vfs(vfs.load_tree(tmp))
        with self.assertRaises(vfs.VfsError):
            fs.change_dir("a.txt")

    def test_cd_relative_from_nested(self):
        fs = self._vfs()
        fs.change_dir("d")
        fs.change_dir("e")
        self.assertEqual(fs.path_str(), "/d/e")


class TestChangeDirAbsolute(unittest.TestCase):
    """Навигация абсолютными путями."""

    def _vfs(self):
        tmp = tempfile.mkdtemp()
        _make(tmp, ["d/b.txt", "d/e/c.txt", "x/y/z.txt"])
        return vfs.Vfs(vfs.load_tree(tmp))

    def test_cd_absolute_root(self):
        fs = self._vfs()
        fs.change_dir("d")
        fs.change_dir("/")
        self.assertEqual(fs.path_str(), "/")

    def test_cd_absolute_nested(self):
        fs = self._vfs()
        fs.change_dir("/d/e")
        self.assertEqual(fs.path_str(), "/d/e")

    def test_cd_absolute_switch_branch(self):
        fs = self._vfs()
        fs.change_dir("/d")
        fs.change_dir("/x/y")
        self.assertEqual(fs.path_str(), "/x/y")

    def test_cd_absolute_with_parent(self):
        fs = self._vfs()
        fs.change_dir("/d/e")
        fs.change_dir("/d/e/..")
        self.assertEqual(fs.path_str(), "/d")

    def test_cd_absolute_unknown(self):
        fs = self._vfs()
        with self.assertRaises(vfs.VfsError):
            fs.change_dir("/no/such/path")

    def test_cd_absolute_from_deep(self):
        fs = self._vfs()
        fs.change_dir("/x/y")
        fs.change_dir("/d")
        self.assertEqual(fs.path_str(), "/d")


class TestMixedNavigation(unittest.TestCase):
    """Смешанные сценарии навигации."""

    def _vfs(self):
        tmp = tempfile.mkdtemp()
        _make(tmp, ["a/b/c/d.txt", "a/e/f.txt"])
        return vfs.Vfs(vfs.load_tree(tmp))

    def test_deep_then_back(self):
        fs = self._vfs()
        fs.change_dir("a/b/c")
        self.assertEqual(fs.path_str(), "/a/b/c")
        fs.change_dir("../..")
        self.assertEqual(fs.path_str(), "/a")

    def test_jump_then_relative(self):
        fs = self._vfs()
        fs.change_dir("/a/e")
        fs.change_dir("..")
        fs.change_dir("b")
        self.assertEqual(fs.path_str(), "/a/b")

    def test_root_then_deep(self):
        fs = self._vfs()
        fs.change_dir("/")
        fs.change_dir("a/b/c")
        self.assertEqual(fs.path_str(), "/a/b/c")


if __name__ == "__main__":
    unittest.main()