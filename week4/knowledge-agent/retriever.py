import re
import sys
from pathlib import Path


SUPPORTED = {".md", ".txt"}


def tokenize(text: str) -> set[str]:
    text = text.casefold()
    result = set(re.findall(r"[a-z0-9_]+", text))
    for sequence in re.findall(r"[\u4e00-\u9fff]+", text):
        result.update(sequence[i : i + 2] for i in range(len(sequence) - 1))
    return {token for token in result if token.strip()}


def split_text(text: str, max_chars: int = 600) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    parts = [
        paragraph[start : start + max_chars]
        for paragraph in paragraphs
        for start in range(0, len(paragraph), max_chars)
    ]
    chunks, current = [], ""
    for paragraph in parts:
        if current and len(current) + len(paragraph) + 2 > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks


def load_chunks(root: Path) -> list[dict]:
    chunks = []
    if not root.is_dir():
        return chunks
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.casefold() not in SUPPORTED:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"跳过 {path}: {exc}", file=sys.stderr)
            continue
        for index, content in enumerate(split_text(text), start=1):
            chunks.append({"source": path.relative_to(root).as_posix(), "chunk": index, "text": content})
    return chunks


def search(query: str, chunks: list[dict], limit: int = 3, min_score: float = 0.25) -> list[dict]:
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    scored = []
    for chunk in chunks:
        overlap = query_tokens & tokenize(chunk["text"])
        weight = lambda token: 2 if token.isascii() else 1
        score = sum(weight(token) for token in overlap) / sum(weight(token) for token in query_tokens)
        if score >= min_score:
            scored.append({**chunk, "score": round(score, 4)})
    return sorted(scored, key=lambda item: (-item["score"], item["source"], item["chunk"]))[:limit]


if __name__ == "__main__":
    import json
    import sys

    query = " ".join(sys.argv[1:]).strip()
    if not query:
        raise SystemExit('用法: python retriever.py "问题"')
    print(json.dumps(search(query, load_chunks(Path("knowledge"))), ensure_ascii=False, indent=2))
