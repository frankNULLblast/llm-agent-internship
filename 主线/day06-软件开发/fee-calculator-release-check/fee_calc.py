import argparse
import json
import re
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


FIELDS = {"patent_application_number", "fee_type", "amount_yuan"}
PATENT_NUMBER = re.compile(r"(?:CN)?\d{12}\.[0-9Xx]")
AMOUNT = re.compile(r"(?:0|[1-9]\d*)(?:\.\d{1,2})?")


def parse_amount(value: object) -> Decimal:
    if not isinstance(value, str) or not AMOUNT.fullmatch(value):
        raise ValueError("amount_yuan 必须是最多两位小数的十进制字符串")
    amount = Decimal(value)
    if amount <= 0:
        raise ValueError("amount_yuan 必须大于 0")
    return amount


def format_money(value: Decimal) -> str:
    return f"{value:.2f}"


def calculate(records: object) -> dict:
    if not isinstance(records, list) or not records:
        raise ValueError("输入必须是非空 JSON 数组")

    by_application = defaultdict(lambda: Decimal("0"))
    by_fee_type = defaultdict(lambda: Decimal("0"))
    total = Decimal("0")

    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict) or set(record) != FIELDS:
            raise ValueError(f"第 {index} 条字段必须且只能是：{', '.join(sorted(FIELDS))}")
        number = record["patent_application_number"]
        fee_type = record["fee_type"]
        if not isinstance(number, str) or not PATENT_NUMBER.fullmatch(number):
            raise ValueError(f"第 {index} 条申请号不符合本项目样例格式")
        if not isinstance(fee_type, str) or not fee_type.strip():
            raise ValueError(f"第 {index} 条 fee_type 必须是非空字符串")
        amount = parse_amount(record["amount_yuan"])
        by_application[number] += amount
        by_fee_type[fee_type] += amount
        total += amount

    return {
        "currency": "CNY",
        "record_count": len(records),
        "by_application": {
            key: format_money(value) for key, value in sorted(by_application.items())
        },
        "by_fee_type": {
            key: format_money(value) for key, value in sorted(by_fee_type.items())
        },
        "total_yuan": format_money(total),
    }


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="汇总虚构专利费用记录")
    parser.add_argument("input", type=Path, help="UTF-8 JSON 输入文件")
    parser.add_argument("-o", "--output", type=Path, required=True, help="JSON 输出文件")
    parser.add_argument(
        "--fee-type",
        type=str,
        default=None,
        help="只读筛选：只汇总指定费用类型的记录（不改变默认命令与固定测试）",
    )
    args = parser.parse_args(argv)
    temporary = args.output.with_name(f".{args.output.name}.tmp")
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("输入和输出文件不能相同")
        records = json.loads(args.input.read_text(encoding="utf-8"))
        # 挑战任务：只读 --fee-type 筛选，默认不传则全量；calculate 与固定测试不变
        if args.fee_type is not None and isinstance(records, list):
            records = [
                r for r in records
                if isinstance(r, dict) and r.get("fee_type") == args.fee_type
            ]
        result = calculate(records)
        temporary.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(args.output)
        print(f"已写入 {args.output}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"计算失败：{exc}", file=sys.stderr)
        return 1
    finally:
        if temporary.exists():
            temporary.unlink()


if __name__ == "__main__":
    raise SystemExit(run())
