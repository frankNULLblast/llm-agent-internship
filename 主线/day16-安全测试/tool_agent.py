import ast
import json
import operator
import os
import sys
from pathlib import Path

from openai import OpenAI


NOTES_DIR = Path(__file__).with_name("notes")
MAX_TOOL_ROUNDS = 4
MAX_TOOL_CALLS = 4
OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def reserve_tool_calls(used: int, requested: int) -> int:
    total = used + requested
    if total > MAX_TOOL_CALLS:
        raise RuntimeError(f"超过最大工具调用次数 {MAX_TOOL_CALLS}")
    return total


def calculate(expression: str) -> str:
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 100:
        raise ValueError("表达式为空或过长")

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if abs(node.value) > 1_000_000:
                raise ValueError("数字过大")
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](evaluate(node.left), evaluate(node.right))
        raise ValueError("只允许数字、括号和 + - * /")

    try:
        value = evaluate(ast.parse(expression, mode="eval"))
    except (SyntaxError, TypeError, ZeroDivisionError) as exc:
        raise ValueError(f"无效表达式：{exc}") from exc
    return str(value)


def search_notes(keyword: str) -> str:
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 50:
        raise ValueError("关键词为空或过长")
    matches = []
    for path in sorted(NOTES_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        if keyword.casefold() in text.casefold():
            matches.append(f"{path.name}: {text.strip()}")
    return "\n".join(matches) if matches else "未找到匹配笔记"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算只含数字、括号和加减乘除的算式",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "在授权的本地学习笔记中按关键词只读检索",
            "parameters": {
                "type": "object",
                "properties": {"keyword": {"type": "string"}},
                "required": ["keyword"],
                "additionalProperties": False,
            },
        },
    },
]


def dispatch(name: str, arguments: str) -> str:
    try:
        data = json.loads(arguments)
        if name == "calculate" and set(data) == {"expression"}:
            return calculate(data["expression"])
        if name == "search_notes" and set(data) == {"keyword"}:
            return search_notes(data["keyword"])
        return "工具名或参数不符合约定"
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        return f"工具执行失败：{exc}"


def ask(question: str) -> str:
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("未设置 DEEPSEEK_API_KEY")
    client = OpenAI(api_key=key, base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    messages = [
        {"role": "system", "content": "需要计算或查笔记时使用工具；只依据工具结果回答。"},
        {"role": "user", "content": question},
    ]
    tool_calls_used = 0
    for round_number in range(1, MAX_TOOL_ROUNDS + 1):
        response = client.chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            extra_body={"thinking": {"type": "disabled"}},
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=400,
        )
        message = response.choices[0].message
        messages.append(message)
        if not message.tool_calls:
            return message.content or "模型未返回内容"
        tool_calls_used = reserve_tool_calls(tool_calls_used, len(message.tool_calls))
        for call in message.tool_calls:
            print(f"[tool round={round_number}] {call.function.name} {call.function.arguments}")
            result = dispatch(call.function.name, call.function.arguments)
            print(f"[result] {result}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    raise RuntimeError(f"超过最大工具轮数 {MAX_TOOL_ROUNDS}")


def main() -> int:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print('用法: python tool_agent.py "问题"', file=sys.stderr)
        return 2
    try:
        print(ask(question))
        return 0
    except RuntimeError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
