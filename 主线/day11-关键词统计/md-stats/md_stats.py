import argparse
import re
import sys
from pathlib import Path


IGNORED = {".git", ".venv"}


def markdown_files(root: Path):
    for path in root.rglob("*.md"):
        if not any(part in IGNORED for part in path.parts):
            yield path


def count_keyword(path: Path, keyword: str) -> int:
    text = path.read_text(encoding="utf-8")
    return len(re.findall(re.escape(keyword), text, flags=re.IGNORECASE))


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="统计 Markdown 关键词")
    parser.add_argument("directory", type=Path)
    parser.add_argument("keyword")
    args = parser.parse_args(argv)
    if not args.directory.is_dir():
        print("错误：目录不存在", file=sys.stderr)
        return 1
    if not args.keyword.strip():
        print("错误：关键词不能为空", file=sys.stderr)
        return 1
    total = 0
    for path in sorted(markdown_files(args.directory)):
        try:
            count = count_keyword(path, args.keyword)
        except (OSError, UnicodeDecodeError) as exc:
            print(f"跳过 {path}: {exc}", file=sys.stderr)
            continue
        total += count
        print(f"{path.relative_to(args.directory)}\t{count}")
    print(f"TOTAL\t{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
