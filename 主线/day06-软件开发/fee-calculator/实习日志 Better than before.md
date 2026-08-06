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
![[9a4096e11a192b269f5ed0c603abcf34.png]]
![[d2ac72b374688a6c3fcc3e85f96cd23d.png]]
![[90ac185d4d4b9a4a342125045e569ff9.png]]
金额为什么用 Decimal 不用 float

> 原子笔记 · 关联：[[软件开发六阶段]] ｜ [[原子写文件避免半截输出]] ｜ [[Day6 知识库]]

核心
金额是十进制的，但计算机底层用二进制浮点。很多十进制小数不能精确表示，会产生**不可见误差**：

```python
>>> 0.1 + 0.2
0.30000000000000004   # 不是 0.3
```

如果金额用 `float` 累加，几次之后就会出现"对账对不上"的幽灵误差。

本日做法（三步走）
1. **输入存字符串**：`fees.json` 里金额是 `"3500.00"` 这种字符串，不是数字。
2. **用 `Decimal` 计算**：`Decimal(value)` 精确表达十进制；校验时也卡"最多两位小数、大于 0"。
3. **输出格式化为两位小数字符串**：`f"{value:.2f}"`，保证 `summary.json` 里全是 `"5600.50"` 这种干净字符串。

验收硬要求
- 代码里**不允许出现金额 `float`**；所有金额从字符串来、用 `Decimal` 算、以两位小数字符串出去。
- 这也呼应 Day 4「response_format 与 JSON 校验」：金额写成字符串（如 `"3500.00"`）而不是数字，避免模型/解析把它变成浮点。

一句话
钱不能用 `float` 算——存字符串、用 `Decimal`、输出两位小数字符串，误差才不会出现。
软件开发六阶段：需求-设计-编码-集成-测试-上线

> 原子笔记 · 关联：[[金额用 Decimal 不用 float]] ｜ [[原子写文件避免半截输出]] ｜ [[Day6 知识库]]

核心
Day 6 把"写一个小工具"升级成"走完软件开发全过程"。六阶段各有要回答的问题和可检查证据：

| 阶段 | 要回答的问题 | 可检查证据 |
|---|---|---|
| 需求 | 给谁用、解决什么、什么算完成？ | `REQUIREMENTS.md` + 固定验收样例 |
| 设计 | 数据怎么流、接口和失败行为是什么？ | `DESIGN.md` 数据流与 JSON 契约 |
| 编码 | 最小实现是否忠实需求？ | `fee_calc.py` |
| 集成 | 文件输入/校验/汇总/输出能否连通？ | 固定命令生成 `summary.json` |
| 测试 | 正常/边界/异常是否可重复验证？ | `test_fee_calc.py` + 测试输出 |
| 上线 | 新使用者能否拿到固定版本复现？ | `README` + `v0.1.0` + 新克隆验证 |

不是瀑布
- 关键认知：**不是"做完一阶段就永不回头"**，而是每次变化都重新检查受影响的阶段。
- 小项目也能只用几页文档，但**不能省"输入、输出、验证证据"**三样东西。

本日最小运行观察
- 本地 CLI 没有常驻服务，观察窗口只有：退出码、标准错误、测试输出、`summary.json`。
- 生产环境的监控、告警、自动回滚只讲概念，本项目不实现。

一句话
先写"算什么、怎么算、错怎么办"，再写代码；最后用固定版本让别人复现——这是工程，不是脚本。
原子写文件：避免半截输出

> 原子笔记 · 关联：[[软件开发六阶段]] ｜ [[金额用 Decimal 不用 float]] ｜ [[Day6 知识库]]

核心
写输出文件时，如果"先开文件写一半、中途报错"，就会留下一个**半个 JSON** 或**错误汇总**，上游读它就崩。解决方法是**原子替换**。

本日做法（临时文件 + replace）
```python
temporary = args.output.with_name(f".{args.output.name}.tmp")
try:
    ...
    temporary.write_text(json.dumps(result, ...) + "\n", encoding="utf-8")
    temporary.replace(args.output)   # 整文件一次性替换，要么全有要么全无
    return 0
except (OSError, ValueError) as exc:
    print(f"计算失败：{exc}", file=sys.stderr)
    return 1
finally:
    if temporary.exists():
        temporary.unlink()           # 异常时清理临时文件
```

为什么安全
- 临时文件先写同目录；**只有完整成功才 `replace` 目标**，所以目标文件要么是新完整版、要么保持旧版，绝不会是半截。
- `finally` 里删除临时文件，异常时也不留垃圾；旧 `summary.json` 原样保留（对应需求"失败不得创建或覆盖输出"）。

失败行为对照
| 情况 | 结果 |
|---|---|
| 损坏 JSON / 字段错 / 金额非法 | 退出码 1，旧 `summary.json` 不变，无半截输出 |
| 输入与输出同路径 | 退出码 1，原文件内容不变 |
| 全部成功 | 临时文件 replace 成新 `summary.json`，退出码 0 |

一句话
写文件先写临时、成功才替换、异常必清理——失败不产生半截或不完整的输出。
