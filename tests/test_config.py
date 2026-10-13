"""Тесты для модуля конфигурации."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import config  # noqa: E402


class TestParseArgs(unittest.TestCase):
    """Проверка разбора CLI-аргументов."""

    def test_defaults(self):
        cfg = config.parse_args([])
        self.assertIsNone(cfg.vfs_path)
        self.assertIsNone(cfg.script_path)

    def test_vfs_only(self):
        cfg = config.parse_args(["--vfs", "./data"])
        self.assertTrue(cfg.vfs_path.endswith("data"))

    def test_script_only(self):
        cfg = config.parse_args(["--script", "./demo.txt"])
        self.assertTrue(cfg.script_path.endswith("demo.txt"))

    def test_both(self):
        cfg = config.parse_args(
            ["--vfs", "./data", "--script", "./demo.txt"]
        )
        self.assertTrue(cfg.vfs_path.endswith("data"))
        self.assertTrue(cfg.script_path.endswith("demo.txt"))


class TestValidateConfig(unittest.TestCase):
    """Проверка валидации конфигурации."""

    def test_empty_is_valid(self):
        self.assertEqual(config.validate_config(config.Config()), [])

    def test_missing_vfs(self):
        cfg = config.Config(vfs_path="C:/no/such/path/xyz")
        errors = config.validate_config(cfg)
        self.assertEqual(len(errors), 1)
        self.assertIn("VFS не найдена", errors[0])

    def test_existing_dir_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = config.Config(vfs_path=tmp)
            self.assertEqual(config.validate_config(cfg), [])

    def test_file_instead_of_dir_is_invalid(self):
        with tempfile.NamedTemporaryFile() as fp:
            cfg = config.Config(vfs_path=fp.name)
            errors = config.validate_config(cfg)
            self.assertEqual(len(errors), 1)
            self.assertIn("не директория", errors[0])

    def test_missing_script(self):
        cfg = config.Config(script_path="C:/no/such/file.txt")
        errors = config.validate_config(cfg)
        self.assertEqual(len(errors), 1)
        self.assertIn("Скрипт не найден", errors[0])

    def test_existing_script_is_valid(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as fp:
            cfg = config.Config(script_path=fp.name)
            self.assertEqual(config.validate_config(cfg), [])


class TestFormatDebug(unittest.TestCase):
    """Проверка отладочного вывода."""

    def test_contains_paths(self):
        cfg = config.Config(
            vfs_path="/tmp/vfs",
            script_path="/tmp/s.txt",
        )
        text = config.format_debug(cfg)
        self.assertIn("/tmp/vfs", text)
        self.assertIn("/tmp/s.txt", text)

    def test_placeholder_when_empty(self):
        text = config.format_debug(config.Config())
        self.assertIn("(не задан)", text)


if __name__ == "__main__":
    unittest.main()