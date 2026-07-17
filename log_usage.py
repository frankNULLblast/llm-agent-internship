"""Day 4 挑战任务：把一次成功调用的 Token 用量追加到 usage.jsonl。

每行一个 JSON，只记录用量与时间，不含提示词正文、不含 API Key。
用法：python log_usage.py "你的问题"
"""
import json
import os
import sys
from datetime import datetime, timezone

from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI

USAGE_FILE = "usage.jsonl"


def make_client() -> OpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("未设置 DEEPSEEK_API_KEY，请先按教程安全输入。")
    return OpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        timeout=30.0,
    )


def main() -> int:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print('用法: python log_usage.py "你的问题"')
        return 2
    try:
        response = make_client().chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            extra_body={"thinking": {"type": "disabled"}},
            messages=[
                {"role": "system", "content": "简洁回答；不知道时明确说不知道。"},
                {"role": "user", "content": question},
            ],
            max_tokens=300,
        )
    except AuthenticationError:
        print("认证失败：请检查 API Key。", file=sys.stderr)
        return 3
    except APIConnectionError:
        print("网络连接失败：请检查网络和 Base URL。", file=sys.stderr)
        return 4
    except APIStatusError as exc:
        print(f"API 返回错误：HTTP {exc.status_code}", file=sys.stderr)
        return 5
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 6

    print(response.choices[0].message.content)

    usage = response.usage
    if not usage:
        print("本次调用未返回 usage，未写入文件。", file=sys.stderr)
        return 0

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
    }
    with open(USAGE_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"\n[usage] 已追加到 {USAGE_FILE}：{record}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
