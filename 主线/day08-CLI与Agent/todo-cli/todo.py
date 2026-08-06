import argparse
import json
import os
import sys
from pathlib import Path


DATA_FILE = Path("todos.json")


class FriendlyParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(f"参数错误：{message}")


def parse_id(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("ID 必须是整数") from exc


def load() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("todos.json 格式错误")
    return data


def save(items: list[dict]) -> None:
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, DATA_FILE)


def next_id(items: list[dict]) -> int:
    return max((item["id"] for item in items), default=0) + 1


def find(items: list[dict], item_id: int) -> dict:
    for item in items:
        if item["id"] == item_id:
            return item
    raise ValueError(f"不存在 ID {item_id}")


def run(argv: list[str] | None = None) -> int:
    parser = FriendlyParser(description="简单待办事项")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add")
    add.add_argument("text")
    sub.add_parser("list")
    done = sub.add_parser("done")
    done.add_argument("id", type=parse_id)
    delete = sub.add_parser("delete")
    delete.add_argument("id", type=parse_id)
    sub.add_parser("clear-done")
    try:
        args = parser.parse_args(argv)
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    try:
        items = load()
        if args.command == "add":
            text = args.text.strip()
            if not text:
                raise ValueError("待办内容不能为空")
            item = {"id": next_id(items), "text": text, "done": False}
            items.append(item)
            save(items)
            print(f"已添加 ID {item['id']}")
        elif args.command == "list":
            if not items:
                print("暂无待办")
            for item in items:
                mark = "x" if item["done"] else " "
                print(f"[{mark}] {item['id']}: {item['text']}")
        elif args.command == "done":
            find(items, args.id)["done"] = True
            save(items)
            print(f"已完成 ID {args.id}")
        elif args.command == "delete":
            target = find(items, args.id)
            items.remove(target)
            save(items)
            print(f"已删除 ID {args.id}")
        elif args.command == "clear-done":
            removed = [item for item in items if item["done"]]
            items = [item for item in items if not item["done"]]
            save(items)
            print(f"已清除 {len(removed)} 个已完成事项")
        return 0
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
