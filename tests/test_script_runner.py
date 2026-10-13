"""Тесты для исполнителя стартовых скриптов."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import emulator, script_runner  # noqa: E402


def _write(tmp_dir, name, content):
    """Записать временный файл и вернуть его путь."""
    path = os.path.join(tmp_dir, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return path


class TestReadScriptLines(unittest.TestCase):
    """Проверка чтения и фильтрации строк."""

    def test_skips_comments_and_blanks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, "s.txt", "# c\n\nls\n  \ncd /\n")
            lines = script_runner.read_script_lines(path)
            self.assertEqual(lines, ["ls", "cd /"])

    def test_missing_file_raises(self):
        with self.assertRaises(script_runner.ScriptError):
            script_runner.read_script_lines("C:/no/such/file.txt")


class TestRunScript(unittest.TestCase):
    """Проверка исполнения скрипта."""

    def test_all_commands_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, "s.txt", "ls\npwd\ncd\n")
            count = script_runner.run_script(
                path, emulator.dispatch, emulator.parse_input
            )
            self.assertEqual(count, 3)

    def test_unknown_command_does_not_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, "s.txt", "unknown\nls\npwd\n")
            count = script_runner.run_script(
                path, emulator.dispatch, emulator.parse_input
            )
            self.assertEqual(count, 3)


if __name__ == "__main__":
    unittest.main()