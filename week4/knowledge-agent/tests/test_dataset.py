"""Day 17 数据集自检：不调用 API，只校验需求与数据的一致性。

教程 Day 17 只要求建好骨架，这些测试是自加的加固项。
目的：把验收清单里"10 条问题含可回答与必须拒答两类""每条可回答问题
有期望来源和关键词"变成能重复执行的检查，后面几天改数据集时不会悄悄改坏。
"""

import json
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
QUESTIONS_FILE = PROJECT_ROOT / "test_questions.json"

REQUIRED_FIELDS = ("question", "expected_sources", "must_contain", "should_refuse")
VALID_DIFFICULTY = {"easy", "medium", "hard"}


def load_questions():
    with QUESTIONS_FILE.open(encoding="utf-8") as f:
        return json.load(f)


class TestProjectLayout(unittest.TestCase):
    """骨架文件必须齐全，缺一个后面几天就会卡住。"""

    def test_required_files_exist(self):
        for name in ("REQUIREMENTS.md", "test_questions.json", ".gitignore", ".env.example"):
            with self.subTest(file=name):
                self.assertTrue((PROJECT_ROOT / name).is_file(), f"缺少 {name}")

    def test_knowledge_files_exist(self):
        for name in ("llm.md", "agent.md", "mcp-security.md"):
            with self.subTest(file=name):
                path = KNOWLEDGE_DIR / name
                self.assertTrue(path.is_file(), f"缺少 knowledge/{name}")
                self.assertGreater(len(path.read_text(encoding="utf-8").strip()), 0,
                                   f"knowledge/{name} 是空文件")

    def test_knowledge_files_are_utf8(self):
        """需求写明只读 UTF-8，这里守住这条。"""
        for path in KNOWLEDGE_DIR.glob("*.md"):
            with self.subTest(file=path.name):
                path.read_text(encoding="utf-8")

    def test_gitignore_blocks_secrets_and_artifacts(self):
        content = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in (".env", "eval_results.json", "agent.log", "__pycache__/"):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, content, f".gitignore 没有排除 {pattern}")

    def test_env_example_has_no_real_key(self):
        """.env.example 只能有变量名和公共值，不能带真 Key。"""
        for line in (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
            if line.startswith("DEEPSEEK_API_KEY"):
                self.assertEqual(line.strip(), "DEEPSEEK_API_KEY=", "API Key 不能写进示例文件")


class TestQuestionSet(unittest.TestCase):
    """10 条验收问题是后面四天的标尺，结构不能松。"""

    @classmethod
    def setUpClass(cls):
        cls.questions = load_questions()

    def test_has_ten_questions(self):
        self.assertEqual(len(self.questions), 10)

    def test_has_both_answerable_and_refusal(self):
        answerable = [q for q in self.questions if not q["should_refuse"]]
        refusal = [q for q in self.questions if q["should_refuse"]]
        self.assertGreater(len(answerable), 0, "缺少可回答问题")
        self.assertGreater(len(refusal), 0, "缺少必须拒答问题")

    def test_required_fields_present(self):
        for idx, q in enumerate(self.questions, start=1):
            for field in REQUIRED_FIELDS:
                with self.subTest(question=idx, field=field):
                    self.assertIn(field, q)

    def test_answerable_has_sources_and_keywords(self):
        for idx, q in enumerate(self.questions, start=1):
            if q["should_refuse"]:
                continue
            with self.subTest(question=idx):
                self.assertTrue(q["expected_sources"], f"第 {idx} 题缺期望来源")
                self.assertTrue(q["must_contain"], f"第 {idx} 题缺关键词")

    def test_refusal_questions_have_empty_fields(self):
        for idx, q in enumerate(self.questions, start=1):
            if not q["should_refuse"]:
                continue
            with self.subTest(question=idx):
                self.assertEqual(q["expected_sources"], [], f"第 {idx} 题是拒答题，不该有来源")
                self.assertEqual(q["must_contain"], [], f"第 {idx} 题是拒答题，不该有关键词")

    def test_expected_sources_exist_on_disk(self):
        available = {p.name for p in KNOWLEDGE_DIR.glob("*.md")}
        for idx, q in enumerate(self.questions, start=1):
            for source in q["expected_sources"]:
                with self.subTest(question=idx, source=source):
                    self.assertIn(source, available, f"第 {idx} 题的来源 {source} 不存在")

    def test_keywords_actually_appear_in_sources(self):
        """教程常见错误第 2 条：问题答案不在资料中。这里提前挡掉。"""
        for idx, q in enumerate(self.questions, start=1):
            for keyword in q["must_contain"]:
                with self.subTest(question=idx, keyword=keyword):
                    hit = any(
                        keyword in (KNOWLEDGE_DIR / source).read_text(encoding="utf-8")
                        for source in q["expected_sources"]
                    )
                    self.assertTrue(hit, f"第 {idx} 题关键词「{keyword}」在期望来源里找不到")

    def test_questions_are_unique(self):
        texts = [q["question"] for q in self.questions]
        self.assertEqual(len(texts), len(set(texts)), "有重复问题")

    def test_difficulty_label_is_valid(self):
        """挑战任务：难度标记合法且三档都用上。"""
        labels = set()
        for idx, q in enumerate(self.questions, start=1):
            with self.subTest(question=idx):
                self.assertIn("difficulty", q, f"第 {idx} 题缺 difficulty")
                self.assertIn(q["difficulty"], VALID_DIFFICULTY)
            labels.add(q["difficulty"])
        self.assertEqual(labels, VALID_DIFFICULTY, "三档难度没有全部用上")


if __name__ == "__main__":
    unittest.main(verbosity=2)
