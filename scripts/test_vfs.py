"""Тесты виртуальной файловой системы."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import vfs


def _make(tmp: str, files):
    """Создать структуру файлов в tmp и вернуть путь корня."""
    for rel in files:
        full = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write("")
    return tmp


class TestLoadTree(unittest.TestCase):
    """Проверка загрузки VFS."""

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

    def test_nested(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make(tmp, ["a.txt", "d/b.txt", "d/e/c.txt"])
            root = vfs.load_tree(tmp)
            self.assertIn("a.txt", root.children)
            self.assertIn("d", root.children)
            d = root.children["d"]
            self.assertTrue(d.is_dir)
            self.assertIn("b.txt", d.children)
            self.assertIn("e", d.children)


class TestVfs(unittest.TestCase):
    """Проверка навигации и просмотра."""

    def _vfs(self):
        tmp = tempfile.mkdtemp()
        _make(tmp, ["a.txt", "d/b.txt", "d/e/c.txt"])
        return vfs.Vfs(vfs.load_tree(tmp))

    def test_initial_cwd(self):
        fs = self._vfs()
        self.assertEqual(fs.path_str(), "/")

    def test_listdir_root(self):
        fs = self._vfs()
        names = [n for n, _ in fs.listdir()]
        self.assertEqual(names, ["d", "a.txt"])

    def test_cd_relative(self):
        fs = self._vfs()
        fs.change_dir("d")
        self.assertEqual(fs.path_str(), "/d")

    def test_cd_absolute(self):
        fs = self._vfs()
        fs.change_dir("/d/e")
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
        fs.change_dir(".")
        self.assertEqual(fs.path_str(), "/")

    def test_cd_to_file_fails(self):
        fs = self._vfs()
        with self.assertRaises(vfs.VfsError):
            fs.change_dir("a.txt")

    def test_cd_unknown_fails(self):
        fs = self._vfs()
        with self.assertRaises(vfs.VfsError):
            fs.change_dir("no_such_dir")

    def test_nested_path(self):
        fs = self._vfs()
        fs.change_dir("d/e")
        names = [n for n, _ in fs.listdir()]
        self.assertEqual(names, ["c.txt"])


if __name__ == "__main__":
    unittest.main()