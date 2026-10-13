"""Тесты для эмулятора оболочки.
    - парсер ввода;
    - команды без VFS (должны сообщать об ошибке);
    - команды с VFS (ls, cd, pwd);
    - формирование приглашения;
    - диспетчер команд.
"""

import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import emulator, vfs


def _make_vfs(files):
    """Создать временную VFS с указанными файлами и вернуть Vfs.

    :param files: список относительных путей (например, ["d/a.txt"]).
    """
    tmp = tempfile.mkdtemp()
    for rel in files:
        full = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write("")
    return vfs.Vfs(vfs.load_tree(tmp))


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


class TestCommandsWithoutVfs(unittest.TestCase):
    """Команды без VFS должны сообщать об ошибке."""

    def set_up(self):
        emulator.CONTEXT.vfs = None

    def test_ls_no_vfs(self):
        with mock.patch("sys.stderr"):
            status = emulator.cmd_ls([])
        self.assertEqual(status, emulator.EXIT_SUCCESS)

    def test_cd_no_vfs(self):
        with mock.patch("sys.stderr"):
            status = emulator.cmd_cd(["/tmp"])
        self.assertEqual(status, emulator.EXIT_SUCCESS)

    def test_pwd_no_vfs(self):
        with mock.patch("sys.stderr"):
            status = emulator.cmd_pwd([])
        self.assertEqual(status, emulator.EXIT_SUCCESS)


class TestCommandsWithVfs(unittest.TestCase):
    """Команды с VFS: ls, cd, pwd."""

    def set_up(self):
        emulator.CONTEXT.vfs = _make_vfs(
            ["a.txt", "d/b.txt", "d/e/c.txt"]
        )

    def tear_down(self):
        emulator.CONTEXT.vfs = None

    def test_pwd_initial(self):
        with mock.patch("builtins.print") as mocked:
            emulator.cmd_pwd([])
        mocked.assert_called_once_with("/")

    def test_ls_root(self):
        with mock.patch("builtins.print") as mocked:
            emulator.cmd_ls([])
        printed = [call.args[0] for call in mocked.call_args_list]
        self.assertEqual(printed, ["d/", "a.txt"])

    def test_cd_and_pwd(self):
        emulator.cmd_cd(["d"])
        with mock.patch("builtins.print") as mocked:
            emulator.cmd_pwd([])
        mocked.assert_called_once_with("/d")

    def test_cd_absolute(self):
        emulator.cmd_cd(["/d/e"])
        self.assertEqual(
            emulator.CONTEXT.vfs.path_str(),
            "/d/e",
        )

    def test_cd_parent(self):
        emulator.cmd_cd(["d/e"])
        emulator.cmd_cd([".."])
        self.assertEqual(
            emulator.CONTEXT.vfs.path_str(),
            "/d",
        )

    def test_cd_unknown(self):
        with mock.patch("sys.stderr"):
            status = emulator.cmd_cd(["no_such_dir"])
        self.assertEqual(status, emulator.EXIT_SUCCESS)
        self.assertEqual(
            emulator.CONTEXT.vfs.path_str(),
            "/",
        )

    def test_cd_too_many_args(self):
        with mock.patch("sys.stderr"):
            status = emulator.cmd_cd(["a", "b"])
        self.assertEqual(status, emulator.EXIT_SUCCESS)
        self.assertEqual(
            emulator.CONTEXT.vfs.path_str(),
            "/",
        )

    def test_ls_nested(self):
        emulator.cmd_cd(["d"])
        with mock.patch("builtins.print") as mocked:
            emulator.cmd_ls([])
        printed = [call.args[0] for call in mocked.call_args_list]
        self.assertEqual(printed, ["e/", "b.txt"])


class TestDispatch(unittest.TestCase):
    """Проверка диспетчера команд."""

    def set_up(self):
        emulator.CONTEXT.vfs = _make_vfs(["x.txt"])

    def tear_down(self):
        emulator.CONTEXT.vfs = None

    def test_unknown_command(self):
        with mock.patch("sys.stderr"):
            status = emulator.dispatch("nope", [])
        self.assertEqual(status, emulator.EXIT_SUCCESS)

    def test_ls_via_dispatch(self):
        with mock.patch("builtins.print"):
            status = emulator.dispatch("ls", [])
        self.assertEqual(status, emulator.EXIT_SUCCESS)

    def test_exit(self):
        status = emulator.dispatch("exit", [])
        self.assertEqual(status, emulator.EXIT_FAILURE)

    def test_help(self):
        with mock.patch("builtins.print"):
            status = emulator.dispatch("help", [])
        self.assertEqual(status, emulator.EXIT_SUCCESS)


class TestPrompt(unittest.TestCase):
    """Проверка формирования приглашения."""

    def set_up(self):
        emulator.CONTEXT.vfs = None

    def test_prompt_contains_at_and_dollar(self):
        prompt = emulator.build_prompt()
        self.assertIn("@", prompt)
        self.assertTrue(prompt.endswith("$ "))

    def test_prompt_with_vfs(self):
        emulator.CONTEXT.vfs = _make_vfs(["a.txt"])
        emulator.cmd_cd(["/"])
        prompt = emulator.build_prompt()
        self.assertIn(":/$ ", prompt)
        emulator.CONTEXT.vfs = None


if __name__ == "__main__":
    unittest.main()