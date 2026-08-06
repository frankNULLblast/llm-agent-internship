import json
import os
import sys

from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI


def main() -> int:
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        print("未设置 DEEPSEEK_API_KEY", file=sys.stderr)
        return 2
    text = " ".join(sys.argv[1:]).strip()
    if not text:
        print('用法: python extract_json.py "姓名与课程信息"')
        return 2
    client = OpenAI(api_key=key, base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    try:
        response = client.chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            extra_body={"thinking": {"type": "disabled"}},
            messages=[
                {
                    "role": "system",
                    "content": (
                        '只输出 JSON 对象，字段为 name、course、score。'
                        'score 必须是整数；未知字段用 null，不得猜测。'
                    ),
                },
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_object"},
            max_tokens=150,
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

    content = response.choices[0].message.content
    if not content:
        print("模型返回空内容，请重试。", file=sys.stderr)
        return 3
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        print(f"模型返回的内容不是有效 JSON：{exc}", file=sys.stderr)
        return 3
    required = {"name", "course", "score"}
    if type(data) is not dict or set(data) != required or type(data["score"]) not in (int, type(None)):
        print(f"JSON 字段或类型不符合约定：{data}", file=sys.stderr)
        return 4
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
