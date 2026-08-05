import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from openai import APIError, OpenAI

from retriever import load_chunks, search
from tools import TOOL_SCHEMAS, dispatch_tool


KNOWLEDGE_DIR = Path(__file__).with_name("knowledge")
LOG_FILE = Path(__file__).with_name("agent.log")
MAX_TOOL_ROUNDS = 3
MAX_TOOL_CALLS = 3
REFUSAL = "资料不足，无法回答。"


def build_context(results: list[dict]) -> str:
    return "\n\n".join(f"[来源: {item['source']}#{item['chunk']}]\n{item['text']}" for item in results)


def log_tool(name: str, ok: bool) -> None:
    record = {
        "time": datetime.now(timezone.utc).isoformat(),
        "tool": name,
        "ok": ok,
    }
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def looks_like_calculation(question: str) -> bool:
    return bool(re.search(r"\d\s*[+\-*/]\s*\d", question))


def reserve_tool_calls(used: int, requested: int) -> int:
    total = used + requested
    if total > MAX_TOOL_CALLS:
        raise RuntimeError(f"超过最大工具调用次数 {MAX_TOOL_CALLS}")
    return total


def answer(question: str) -> dict:
    question = question.strip()
    if not question:
        raise ValueError("问题不能为空")
    results = search(question, load_chunks(KNOWLEDGE_DIR))
    calculation = looks_like_calculation(question)
    if not results and not calculation:
        return {"answer": REFUSAL, "sources": [], "refused": True, "usage": {"total_tokens": 0}}

    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("未设置 DEEPSEEK_API_KEY")
    context = build_context(results) if results else "本题是算术工具任务，没有知识库上下文。"
    sources = sorted({item["source"] for item in results})
    messages = [
        {
            "role": "system",
            "content": (
                "你是学习资料问答助手。只依据给定上下文和工具结果回答；"
                "不得补充上下文外事实；简洁回答。\n\n" + context
            ),
        },
        {"role": "user", "content": question},
    ]
    client = OpenAI(api_key=key, base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"), timeout=30.0)
    total_tokens = 0
    tool_calls_used = 0
    force_calculator = calculation
    for round_number in range(1, MAX_TOOL_ROUNDS + 1):
        tool_choice = {"type": "function", "function": {"name": "calculate"}} if force_calculator else "auto"
        response = client.chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            extra_body={"thinking": {"type": "disabled"}},
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice=tool_choice,
            max_tokens=400,
        )
        force_calculator = False
        if response.usage:
            total_tokens += response.usage.total_tokens
        message = response.choices[0].message
        messages.append(message)
        if not message.tool_calls:
            return {
                "answer": message.content or REFUSAL,
                "sources": sources,
                "refused": False,
                "usage": {"total_tokens": total_tokens},
            }
        tool_calls_used = reserve_tool_calls(tool_calls_used, len(message.tool_calls))
        for call in message.tool_calls:
            result, ok = dispatch_tool(call.function.name, call.function.arguments)
            log_tool(call.function.name, ok)
            print(f"[tool round={round_number}] {call.function.name}: {result}", file=sys.stderr)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    raise RuntimeError(f"超过最大工具轮数 {MAX_TOOL_ROUNDS}")


def main() -> int:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print('用法: python agent.py "问题"', file=sys.stderr)
        return 2
    try:
        result = answer(question)
        print(result["answer"])
        if result["sources"]:
            print("\n来源：" + ", ".join(result["sources"]))
        print(f"[usage] total={result['usage']['total_tokens']}")
        return 0
    except (ValueError, RuntimeError, OSError, APIError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
