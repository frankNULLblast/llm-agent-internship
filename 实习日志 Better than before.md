# Day 6 每日总结

日期：2026-07-17（星期五）

## 今日完成
- 按教程完成 Day 6「软件开发全过程与专利费用计算器」，严格走**需求 → 设计 → 编码 → 集成 → 测试 → 上线**六阶段。
- 交付一个可复现的专利费用批次计算 CLI（仅用 Python 3.11 标准库，不装新包）。
- 仓库 `software-process/day06/fee-calculator/`：`REQUIREMENTS.md` / `DESIGN.md` / `fees.json` / `fee_calc.py` / `test_fee_calc.py` / `README.md` / `RELEASE_CHECKLIST.md`。
- 挑战任务：新增只读 `--fee-type` 筛选参数，默认命令、JSON Schema 与 9 个固定测试保持不变。
- 完成本地发布：打不可移动标签 `v0.1.0`，并从新克隆目录 `fee-calculator-release-check` 复现验证。

## 验证结果（诚实记录）
- ✅ `python -m py_compile`：编译通过。
- ✅ `python -m unittest -v`：**9 个固定测试全部 OK**（正常汇总 / 空数组 / 缺字段 / 多字段 / 非法金额 / 错申请号 / 损坏 JSON 不覆盖输出 / 输入输出同路径 / CLI 写合法 JSON）。
- ✅ 集成命令 `python fee_calc.py fees.json -o summary.json` → 退出码 0；`summary.json` 总额 `5600.50`、`CN202410123456.7` 小计 `4400.50`、代理服务费 `4700.00`，全部两位小数字符串。
- ✅ 本地克隆复现：在 `fee-calculator-release-check` 跑 9 测试 OK、总额 `5600.50` 复现。
- ✅ 标签复验：`git checkout v0.1.0` 后 9 测试 OK、总额 `5600.50`、`git describe --tags --exact-match` 返回 `v0.1.0`。
- ✅ 挑战任务 `--fee-type 代理服务费`：输出 `record_count=2`、代理服务费 `4700.00`、总额 `4700.00`，不影响全量结果。

## 六阶段证据表

| 阶段 | 文件或命令 | 实际证据 | 仍有的限制 |
|---|---|---|---|
| 需求 | `REQUIREMENTS.md` | 含用户、输入、输出、错误、非目标、固定验收（总额 5600.50） | — |
| 设计 | `DESIGN.md` | 数据流 + 三函数接口（`parse_amount`/`calculate`/`run`）+ 失败写文件边界（临时文件 replace） | — |
| 编码 | `fee_calc.py` | 最小实现；全程 `Decimal`，代码中无 `float` | — |
| 集成 | `python fee_calc.py fees.json -o summary.json` | 退出码 0，`summary.json` 总额 5600.50 | — |
| 测试 | `python -m unittest -v` | 9 测试全部 OK | 挑战 `--fee-type` 仅 CLI 演示，未加入固定测试 |
| 上线 | `v0.1.0`、新克隆验证 | 克隆目录 9 测试 OK、总额 5600.50 复现；`git describe` = v0.1.0 | 仅本地发布，无监控/告警/自动回滚（教程只讲概念） |

## 三个我现在能讲清楚的概念
1. **软件开发六阶段不是瀑布**：不是"做完一阶段永不回头"，而是每次变化都重新检查受影响的阶段；小项目也能用几页文档，但不能省"输入、输出、验证证据"。
2. **金额用 Decimal 不用 float**：`0.1 + 0.2` 这类十进制金额用二进制浮点会有不可见误差；本项目把金额存成字符串，`Decimal` 计算，输出再格式化为两位小数字符串。
3. **原子写文件避免半截输出**：先写同目录临时文件，完整成功后再 `replace` 目标；异常时清理临时文件、保留旧结果——失败绝不产生半个或不完整的 `summary.json`。

## 卡住的点与处理
- **Windows 行尾 CRLF 警告**：`git` 提示 `LF will be replaced by CRLF`，是 Windows 行尾自动转换的提示，不影响功能，未处理。
- **venv 路径**：本机 venv 在 `llm-agent-internship/.venv/Scripts/python.exe`，不是 `$HOME/.venv`；运行前用完整路径调用。
- **挑战任务不动固定接口**：`--fee-type` 只在 `run` 内、且仅当用户传入时才过滤记录列表；`calculate` 与 9 个固定测试一行未改。

## 挑战任务处理
- 要求：增加只读 `--fee-type` 筛选，但默认命令、JSON Schema 与全部固定测试保持不变。
- 做法：`argparse` 加可选 `--fee-type`；在 `run` 里对记录列表做只读过滤后再交给 `calculate`。`calculate` 签名与行为完全不变，9 测试照旧通过。
- 验证：传入 `代理服务费` 得 `record_count=2`、总额 `4700.00`，全量默认结果不变。

## 明日计划
- Day 7：用 Codex 与腾讯 WorkBuddy 完成小改动，比较两工具的计划/审批/结果差异，并映射到六阶段。
- FastAPI 加餐（Day 6 之后）：把 Day 5 的抽取逻辑或本日计算器包成 API 服务。
- 把本日"先文档与测试样例、后编码与发布"的顺序养成习惯，带入第二周。

## 成果附件
- 本日无运行截图（纯 CLI）；证据见 [[实践记录（可截图对照）]] 的命令与输出，及 `summary.json` 内容（总额 5600.50）。
- 六阶段证据表见上方；详细概念见 [[Day6 知识库]]。
