import tempfile
import unittest
from pathlib import Path

from md_stats import count_keyword, markdown_files, run


class MarkdownStatsTests(unittest.TestCase):
    def test_case_insensitive_literal_count(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "a.md"
            path.write_text("Agent agent AGENT a.gent", encoding="utf-8")
            self.assertEqual(count_keyword(path, "agent"), 3)
            self.assertEqual(count_keyword(path, "a.gent"), 1)

    def test_ignored_directory(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "ok.md").write_text("x", encoding="utf-8")
            (root / ".git").mkdir()
            (root / ".git" / "ignored.md").write_text("x", encoding="utf-8")
            self.assertEqual([p.name for p in markdown_files(root)], ["ok.md"])

    def test_missing_directory(self) -> None:
        self.assertEqual(run(["missing-directory", "agent"]), 1)


if __name__ == "__main__":
    unittest.main()
