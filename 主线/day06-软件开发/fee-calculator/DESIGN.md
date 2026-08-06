# 设计

## 数据流

fees.json
  → UTF-8 读取
  → JSON 解析
  → 数组与精确字段校验
  → 申请号、费用类型与 Decimal 金额校验
  → 按申请号/费用类型汇总
  → 统一格式化为两位小数
  → 同目录临时文件
  → 原子替换 summary.json

## 接口

- `parse_amount(value: object) -> Decimal`：只接受合法金额字符串。
- `calculate(records: object) -> dict`：全量校验并返回可序列化汇总。
- `run(argv: list[str] | None = None) -> int`：处理 CLI、文件读写和退出码。

## 失败策略

解析、校验或计算失败时，`calculate` 抛出 `ValueError`；`run` 输出一行中文错误并返回 1。输出先写同目录临时文件，完整成功后再替换目标；异常时清理临时文件并保留旧结果。

## 简化边界

本项目只处理小型本地 JSON，使用一次性内存汇总。数据大到无法放入内存时再考虑流式处理。
