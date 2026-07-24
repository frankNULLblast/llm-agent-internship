import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import todo


class TodoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp.name) / "todos.json"
        self.data_patch = patch.object(todo, "DATA_FILE", self.data_file)
        self.data_patch.start()

    def tearDown(self) -> None:
        self.data_patch.stop()
        self.temp.cleanup()

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = todo.run(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_add_and_list_persist(self) -> None:
        code, output, error = self.run_cli("add", "阅读文档")
        self.assertEqual((code, output, error), (0, "已添加 ID 1\n", ""))
        code, output, _ = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertEqual(output, "[ ] 1: 阅读文档\n")
        self.assertEqual(json.loads(self.data_file.read_text(encoding="utf-8"))[0]["text"], "阅读文档")

    def test_blank_text_fails(self) -> None:
        code, _, error = self.run_cli("add", "   ")
        self.assertEqual(code, 1)
        self.assertIn("不能为空", error)
        self.assertFalse(self.data_file.exists())

    def test_done_and_delete(self) -> None:
        self.run_cli("add", "任务")
        self.assertEqual(self.run_cli("done", "1")[0], 0)
        self.assertIn("[x] 1", self.run_cli("list")[1])
        self.assertEqual(self.run_cli("delete", "1")[0], 0)
        self.assertEqual(self.run_cli("list")[1], "暂无待办\n")

    def test_missing_id_fails(self) -> None:
        code, _, error = self.run_cli("done", "99")
        self.assertEqual(code, 1)
        self.assertIn("不存在 ID 99", error)

    def test_non_integer_id_fails(self) -> None:
        code, _, error = self.run_cli("done", "abc")
        self.assertEqual(code, 1)
        self.assertIn("ID 必须是整数", error)

    def test_invalid_json_fails(self) -> None:
        self.data_file.write_text("not json", encoding="utf-8")
        code, _, error = self.run_cli("list")
        self.assertEqual(code, 1)
        self.assertIn("错误", error)

    def test_save_oserror_reports_failure(self) -> None:
        # 挑战：磁盘写入失败时不应误报成功（code 必须是 1）
        with patch.object(todo, "save", side_effect=OSError("磁盘写满")):
            code, _, error = self.run_cli("add", "任务")
        self.assertEqual(code, 1)
        self.assertIn("错误", error)
        self.assertFalse(self.data_file.exists())


if __name__ == "__main__":
    unittest.main()
