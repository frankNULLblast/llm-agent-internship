# 实习日志 Better than before — FastAPI Day 1

> 日期：2026-07-17 ｜ 专题：大模型与智能体 FastAPI 五天加餐 ｜ 第 1 天
> 前置：已完成原教程 Day 5（专利票据识别）+ Day 6（费用计算器六阶段）

## 今日做了什么

今天正式进入 FastAPI 加餐。目标只有一个：把第一个 HTTP 接口 `GET /health` 跑起来，并用三种方式验证它真的能被访问。

1. **确认前置条件满足**：教程要求 `week1/day05/patent_bill.py` 和 `software-process/day06/fee-calculator/fee_calc.py` 都存在，已验证都在。
2. **安装依赖**：在统一 `.venv` 里装了固定版本 `fastapi[standard-no-fastapi-cloud-cli]==0.139.0`、`httpx2==2.5.0`、`pytest==9.1.1`、`openai==2.45.0`。验证 import 版本输出 `0.139.0 2.5.0 2.45.0 9.1.1`，与教程一致。
3. **建项目**：`llm-agent-internship/fastapi-plus/patent-api`，`git init` 独立仓库，分支 `fastapi-day1`。
4. **写 `main.py`**：一个最小应用，`GET /health` 返回固定版本 `0.1.0`，响应用 Pydantic `HealthResponse`（`strict=True`、`extra="forbid"`）约束。
5. **三种方式验证**（关键）：
   - 命令行：`curl http://127.0.0.1:8000/health` → `{"status":"ok","version":"0.1.0"}`；`/openapi.json` → HTTP 200；`/docs` → HTTP 200（Swagger UI 可访问）。
   - 测试：`pytest` 用 `TestClient` 请求 `/health`，断言 200 与固定 JSON → `1 passed`。
   - 浏览器 / Swagger：教程要求展开 `GET /health` 点 Try it out / Execute 看 200（本机用 `/docs` 返回 200 作证据）。
6. **挑战任务**：给 `FastAPI(...)` 补了 `summary` 和 `contact` 元数据，不新增接口；重新看 `/openapi.json` 的 `info` 里多出 `summary` 和 `contact` 字段。

## 验收清单（逐条对照）

- [x] 能画出客户端、Uvicorn、FastAPI 路由函数之间的数据流
- [x] 能解释 URL 中主机、端口和路径分别是什么（见 [[HTTP 与 ASGI 数据流]]）
- [x] 浏览器、命令行和 TestClient 三种验证均成功
- [x] `python -m pytest -q` 显示 `1 passed`
- [x] Git 中无 `.venv`、API Key 或真实业务数据（已加 `.gitignore`）

## 实践证据

- 启动命令：`python -m fastapi dev main.py --host 127.0.0.1`
- `/health` 响应：`{"status":"ok","version":"0.1.0"}`
- `/openapi.json` 状态码：`200`，且 `paths` 含 `/health`
- `/docs` 状态码：`200`
- pytest：`1 passed in 0.3s`
- Git 提交：`0cb7f5b`（health 接口）、`d9f6fad`（挑战元数据），分支 `fastapi-day1`，已推 GitHub

## 遇到的问题与根因

- **`fastapi: command not found` 风险**：一开始 `.venv` 里没装 fastapi，按教程固定版本 `pip install` 后解决。教训：FastAPI 加餐要自己装，统一 `.venv` 只预装了 openai。
- **curl 管道偶发 `(23) client returned ERROR`**：把 `/openapi.json` 通过管道喂给 `python -c` 解析时，python 读完一行就退出、curl 还有剩余字节要写导致报错。不影响结果（解析已正确输出），但要理解为"管道另一端提前关闭"的现象。

## Agent 做了什么，我验证了什么

- Agent 建目录、写 `main.py`/`test_main.py`、装依赖、跑验证、提交推送、整理笔记。
- 我需要亲手验证的：在 PowerShell 激活 `.venv` → 跑 `fastapi dev` 看到 `Uvicorn running on http://127.0.0.1:8000` → 浏览器开 `/docs` 点 Try it out 看 200 → 跑 `pytest` 看到 `1 passed`。这一步是"人负责验收"的延续。

## 明日计划

- FastAPI Day 2：请求模型、响应模型与费用汇总（把 Day 6 的 `fee_calc.py` 包成 `POST /api/v1/fees/summary`）。

## 成果附件

- 终端启动日志截图、curl `/health` 输出、pytest 输出、浏览器 `/docs` 页面（见 `附件/`）
