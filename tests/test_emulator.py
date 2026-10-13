"""Тесты для этапа 1 эмулятора оболочки."""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import emulator  # noqa: E402


class TestParseInput(unittest.TestCase):
    """Проверка парсера ввода."""

    def test_empty(self):
        self.assertEqual(emulator.parse_input("   "), (None, []))

    def test_command_only(self):
        self.assertEqual(emulator.parse_input("ls"), ("ls", []))

    def test_command_with_args(self):
        self.assertEqual(
            emulator.parse_input("ls -la /tmp"),
            ("ls", ["-la", "/tmp"]),
        )


class TestDispatch(unittest.TestCase):
    """Проверка диспетчера команд."""

    def test_unknown_command(self):
        with mock.patch("sys.stderr"):
            status = emulator.dispatch("nope", [])
        self.assertEqual(status, emulator.EXIT_SUCCESS)

    def test_ls_stub(self):
        status = emulator.dispatch("ls", ["-l"])
        self.assertEqual(status, emulator.EXIT_SUCCESS)

    def test_cd_too_many_args(self):
        status = emulator.dispatch("cd", ["a", "b"])
        self.assertEqual(status, emulator.EXIT_SUCCESS)

    def test_exit(self):
        status = emulator.dispatch("exit", [])
        self.assertEqual(status, emulator.EXIT_FAILURE)


class TestPrompt(unittest.TestCase):
    """Проверка формирования приглашения."""

    def test_prompt_contains_at_and_dollar(self):
        prompt = emulator.build_prompt()
        self.assertIn("@", prompt)
        self.assertTrue(prompt.endswith("$ "))


if __name__ == "__main__":
    unittest.main()