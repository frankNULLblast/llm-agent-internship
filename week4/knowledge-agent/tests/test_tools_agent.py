import unittest

from agent import REFUSAL, answer, build_context, reserve_tool_calls
from tools import calculate, dispatch_tool


class ToolAndAgentTests(unittest.TestCase):
    def test_calculate(self) -> None:
        self.assertEqual(calculate("(12+8)/4"), "5.0")

    def test_calculator_rejects_code(self) -> None:
        with self.assertRaises(ValueError):
            calculate("__import__('os')")

    def test_dispatch_rejects_unknown_tool(self) -> None:
        result, ok = dispatch_tool("delete_files", "{}")
        self.assertFalse(ok)
        self.assertIn("不符合约定", result)

    def test_context_contains_source(self) -> None:
        context = build_context([{"source": "a.md", "chunk": 2, "text": "内容"}])
        self.assertIn("[来源: a.md#2]", context)

    def test_unknown_question_refuses_without_api(self) -> None:
        result = answer("食堂今天供应什么菜？")
        self.assertEqual(result["answer"], REFUSAL)
        self.assertTrue(result["refused"])
        self.assertEqual(result["usage"]["total_tokens"], 0)

    def test_tool_call_budget_is_enforced(self) -> None:
        self.assertEqual(reserve_tool_calls(0, 3), 3)
        with self.assertRaises(RuntimeError):
            reserve_tool_calls(3, 1)


if __name__ == "__main__":
    unittest.main()
