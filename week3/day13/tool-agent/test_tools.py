"""Day 13 挑战任务：为 calculate 和 search_notes 各写 3 个 unittest，包括恶意输入。"""

import unittest

from tool_agent import calculate, search_notes


class TestCalculate(unittest.TestCase):
    """安全计算器：正常运算、恶意注入、边界异常。"""

    def test_normal_arithmetic(self):
        """正常四则运算返回正确数值字符串。"""
        self.assertEqual(calculate("(12+8)/4"), "5.0")
        self.assertEqual(calculate("2*3+1"), "7")
        self.assertEqual(calculate("-10+5"), "-5")

    def test_malicious_import_rejected(self):
        """__import__ 等危险表达式必须被拒绝，绝不执行系统命令。"""
        with self.assertRaises(ValueError):
            calculate("__import__('os').system('whoami')")
        with self.assertRaises(ValueError):
            calculate("open('secret.txt').read()")

    def test_division_by_zero(self):
        """除零应抛出 ValueError，而非崩溃或返回 nan。"""
        with self.assertRaises(ValueError):
            calculate("1/0")


class TestSearchNotes(unittest.TestCase):
    """只读笔记检索：命中、未命中、空关键词。"""

    def test_hit_keyword(self):
        """存在的关键词应返回对应笔记文件名和内容。"""
        result = search_notes("参数")
        self.assertIn("agent.txt", result)
        self.assertIn("工具参数必须校验", result)

    def test_no_match(self):
        """不存在的关键词应明确返回未找到，不编造笔记。"""
        result = search_notes("量子芯片")
        self.assertEqual(result, "未找到匹配笔记")

    def test_empty_keyword_rejected(self):
        """空关键词或纯空格应被拒绝。"""
        with self.assertRaises(ValueError):
            search_notes("")
        with self.assertRaises(ValueError):
            search_notes("   ")


if __name__ == "__main__":
    unittest.main()
