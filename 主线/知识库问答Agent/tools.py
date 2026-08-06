import ast
import json
import operator


OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def calculate(expression: str) -> str:
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 100:
        raise ValueError("表达式为空或过长")

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if abs(node.value) > 1_000_000:
                raise ValueError("数字过大")
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](visit(node.left), visit(node.right))
        raise ValueError("只允许数字、括号和 + - * /")

    try:
        return str(visit(ast.parse(expression, mode="eval")))
    except (SyntaxError, ZeroDivisionError) as exc:
        raise ValueError(f"无效表达式：{exc}") from exc


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算只含数字、括号和加减乘除的表达式",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
                "additionalProperties": False,
            },
        },
    }
]


def dispatch_tool(name: str, arguments: str) -> tuple[str, bool]:
    try:
        data = json.loads(arguments)
        if name != "calculate" or set(data) != {"expression"}:
            raise ValueError("工具名或参数不符合约定")
        return calculate(data["expression"]), True
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return f"工具执行失败：{exc}", False
