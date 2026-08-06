import os
import sys

from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI


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
        print('用法: python chat_once.py "你的问题"')
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
    if response.usage:
        print(
            f"\n[usage] input={response.usage.prompt_tokens} "
            f"output={response.usage.completion_tokens} total={response.usage.total_tokens}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
