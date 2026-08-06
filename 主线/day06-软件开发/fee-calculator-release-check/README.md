# Patent Fee Calculator

读取虚构专利费用 JSON，输出按申请号、费用类型和全部记录汇总的 CNY 金额。

## 环境

- Python 3.11
- 仅使用标准库

## 运行（Windows PowerShell 7）

```powershell
python fee_calc.py fees.json -o summary.json
Get-Content summary.json
```

## 运行（Linux Bash）

```bash
python fee_calc.py fees.json -o summary.json
cat summary.json
```

## 测试（Windows/Linux 共用）

```console
python -m unittest -v
```

## 输入约定

输入是非空 JSON 数组。每条记录只包含 `patent_application_number`、`fee_type` 和字符串 `amount_yuan`；金额必须大于 0 且最多两位小数。

## 只读筛选（挑战任务）

```console
python fee_calc.py fees.json -o summary.json --fee-type 代理服务费
```

只汇总指定费用类型的记录；不传 `--fee-type` 时行为与原固定命令、JSON Schema 和 9 个固定测试完全一致。

## 已知限制

- 只处理小型本地 JSON 和 CNY。
- 申请号只检查教学样例格式，不代表官方有效性。
- 不验证真实费用、票据或专利法律状态。
