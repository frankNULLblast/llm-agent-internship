# 实习日志 Better than before — FastAPI Day 2

> 日期：2026-07-21 ｜ 专题：大模型与智能体 FastAPI 五天加餐 ｜ 第 2 天
> 前置：FastAPI Day 1（`/health` + 测试 + 文档）、Day 6 的 `fee_calc.calculate` 可用

## 今日做了什么

Day 2 把 Day 6 的费用汇总逻辑包成了 HTTP 接口，让客户端用 `POST` 把费用记录交进来、拿回汇总结果。

1. **确认前置**：Day 6 的 `software-process/day06/fee-calculator/fee_calc.py` 里的 `calculate(records)` 是纯函数（不碰文件/argv），可以直接复用；Day 1 的 `main.py` / `test_main.py` / `.venv` 都已就位。
2. **复用业务逻辑**：在 `main.py` 顶部用 `sys.path.insert` 把 `fee_calc.py` 目录挂上，直接 `from fee_calc import calculate`，没有复制任何算账代码（业务规则只留一份）。
3. **写请求模型**：`FeeRecord`（单条记录，三个字段）和 `FeeSummaryRequest`（包一层 `records` 列表）；`amount_yuan` 用 `str` 直接对接 `calculate` 的 `parse_amount` 校验。
4. **写响应模型**：`FeeSummaryResponse` 用 `strict=True` + `extra="forbid"`，字段和 `calculate` 的返回对齐（`currency` / `record_count` / `by_application` / `by_fee_type` / `total_yuan`）。
5. **写端点**：`POST /api/v1/fees/summary`，把请求体记录转成 dict 交给 `calculate`，`ValueError` 接住后映射成 HTTP `422`。
6. **补测试**：`test_main.py` 新增三个 `TestClient` 用例——正常汇总 200、非法申请号 422、空数组 422。
7. **三种验证**（延续 Day 1）：
   - 测试：`pytest` → `4 passed`（health + 3 个 Day 2 用例）。
   - 文档：`/openapi.json` 的 `paths` 出现 `/api/v1/fees/summary` 且方法是 `post`。
   - 手动验证待我本机启 `fastapi dev` 后浏览器 `/docs` 点 Try it out 看 200——Agent 已跑通 pytest 与 openapi 检查。

## 验收清单（逐条对照）

- [x] 能说清 `POST` 请求体 vs `GET` 查询参数的区别
- [x] 能解释请求模型（收输入）和响应模型（约束输出）的分工
- [x] `calculate` 逻辑只存在于 Day 6 一处，Web 服务只是调用
- [x] 非法输入返回 422 而非 500
- [x] `pytest` 显示 `4 passed`
- [x] `/openapi.json` 含 `/api/v1/fees/summary`

## 实践证据

- 正常请求：`POST /api/v1/fees/summary` body 为 3 条记录（2 个申请号），返回 `total_yuan="350.00"`、`by_application` 两个申请号分别 `150.00` / `200.00`、`by_fee_type` 申请费 `300.00` / 年费 `50.00`。
- pytest：`4 passed in 2.37s`
- OpenAPI paths：`['/api/v1/fees/summary', '/health']`

## 遇到的问题与根因

- **import 跨目录**：`patent-api` 和 `day06/fee-calculator` 是兄弟目录，不能简单 `import fee_calc`。用 `Path(__file__).resolve().parent.parent.parent / "software-process"/"day06"/"fee-calculator"` 拼出绝对目录再 `sys.path.insert`，避免硬编码绝对路径、也避免改 `calculate` 源码。
- **`amount_yuan` 类型**：一开始想用 `float`，会和 `calculate` 的"字符串金额"校验冲突；改回 `str` 后，客户端传数字或字符串都能被 Pydantic coerce 接住，再原样交给 `calculate`。

## Agent 做了什么，我验证了什么

- Agent 改 `main.py` / `test_main.py`、跑 `pytest` 与 openapi 检查、整理笔记。
- 我需要亲手验证的：本机启 `fastapi dev main.py` → 浏览器开 `/docs` 展开 `POST /api/v1/fees/summary` 点 Try it out 贴一条记录看 200 → 跑 `pytest` 看 `4 passed`。

## 明日计划

- FastAPI Day 3：按教程继续（本机已具备"请求/响应模型 + 复用业务函数 + TestClient 验证"的能力，下一步多半是路径/查询参数或持久化，等教程定）。

## 成果附件

（待补截图）
