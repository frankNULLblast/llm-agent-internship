import json
import tempfile
import unittest
from pathlib import Path

from retriever import load_chunks, search, split_text, tokenize


class RetrieverTests(unittest.TestCase):
    def test_tokenize_chinese_and_english(self) -> None:
        tokens = tokenize("Agent 工具调用")
        self.assertIn("agent", tokens)
        self.assertIn("工具", tokens)

    def test_split_respects_paragraphs(self) -> None:
        self.assertEqual(split_text("第一段\n\n第二段", max_chars=4), ["第一段", "第二段"])

    def test_split_slices_one_long_paragraph(self) -> None:
        self.assertEqual(split_text("甲" * 9, max_chars=4), ["甲" * 4, "甲" * 4, "甲"])

    def test_search_returns_source(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "agent.md").write_text("工具调用需要参数校验。", encoding="utf-8")
            results = search("工具参数如何校验", load_chunks(root))
            self.assertEqual(results[0]["source"], "agent.md")
            self.assertIn("参数校验", results[0]["text"])

    def test_no_match_returns_empty(self) -> None:
        chunks = [{"source": "a.md", "chunk": 1, "text": "只讨论 Python"}]
        self.assertEqual(search("量子芯片", chunks), [])

    def test_single_chinese_character_overlap_is_not_a_match(self) -> None:
        chunks = [{"source": "agent.md", "chunk": 1, "text": "模型请求遵循最小权限的工具。"}]
        self.assertEqual(search("请介绍量子芯片的最新型号。", chunks), [])

    def test_bad_encoding_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "good.md").write_text("工具调用", encoding="utf-8")
            (root / "bad.txt").write_bytes(b"\xff")
            self.assertEqual([item["source"] for item in load_chunks(root)], ["good.md"])

    def test_agent_question_only_uses_agent_source(self) -> None:
        chunks = load_chunks(Path("knowledge"))
        sources = {item["source"] for item in search("Agent 的基本组成有哪些？", chunks)}
        self.assertEqual(sources, {"agent.md"})

    def test_fixed_question_set_matches_expected_sources(self) -> None:
        chunks = load_chunks(Path("knowledge"))
        cases = json.loads(Path("test_questions.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(question=case["question"]):
                results = search(case["question"], chunks)
                sources = {item["source"] for item in results}
                if case["should_refuse"]:
                    self.assertEqual(results, [])
                else:
                    self.assertLessEqual(set(case["expected_sources"]), sources)

    def test_missing_directory_is_empty(self) -> None:
        self.assertEqual(load_chunks(Path("missing-knowledge-directory")), [])


if __name__ == "__main__":
    unittest.main()
