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


![[e38762021f054d34a15d5b5711ec0ada.png]]
![[df4388a9daba0fe520dbbd947c8ce94f.png]]
![[5e0fc15e4cc85cd46502104f951634f3.png]]
![[5a2c57483fec704975ec7f44c008241f.png]]
![[4cd7af895a85463da7e6a2b8dd448062.png]]
 HTTP 与 ASGI 数据流

一句话

客户端发 HTTP 请求，Uvicorn 负责监听端口并把请求交给 FastAPI 的路由函数，函数返回值再由 Uvicorn 包成 HTTP 响应送回客户端。

关键名词

| 名词 | 本日含义 | 本项目示例 |
|---|---|---|
| 客户端 | 发出 HTTP 请求的程序 | 浏览器、`curl`、TestClient |
| 服务端 | 接收请求并返回响应的程序 | FastAPI 应用 |
| 方法 | 请求意图 | `GET` 读取、`POST` 提交数据 |
| 路径 | URL 里定位接口的部分 | `/health` |
| 状态码 | 请求处理结果 | `200` 成功、`422` 请求不符合 Schema |
| ASGI | Python Web 应用与服务器的接口规范 | FastAPI 应用交给 Uvicorn 运行 |
| Uvicorn | 加载 ASGI 应用并监听端口的服务器 | `fastapi dev` 内部使用它 |
 一次请求的最小过程

```
客户端 → 127.0.0.1:8000 → Uvicorn → FastAPI 路由函数
客户端 ← 状态码 + JSON ← Uvicorn ← 路由函数返回值
```

- `127.0.0.1` 只指向**当前这台电脑**（本机回环），外网访问不到，开发安全。
- `8000` 是端口，用来区分同一台电脑上的不同网络程序。
- `main:app` 里 `main` 是文件名 `main.py`，`app` 是文件里的 `app = FastAPI(...)` 对象。

为什么是 `async def` 还是 `def`

本日 `health()` 用普通 `def`，因为它只在内存里构造一个小对象、没有 `await` 的异步操作。不要为了"看着现代"机械改成 `async def`。

关联

- [[../Day1 知识库|Day1 知识库]]
- [[TestClient 为什么不需要真实端口]]
Pydantic 响应模型与 strict

今天用到的响应模型

```python
class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    status: Literal["ok"]
    version: str
```

`@app.get("/health", response_model=HealthResponse)` 让 FastAPI 在返回前**用这个模型校验并序列化**返回值。

两个配置的含义

- `strict=True`：**严格类型**。比如 `version` 必须是 `str`，你返回个数字 `0.1.0`（实际是字符串）没问题，但如果你返回 `int` 或类型不符，Pydantic 直接报错而不是默默转换。它逼你类型对齐。
- `extra="forbid"`：**禁止多余字段**。返回体里多一个字段就报错。防止"顺手多塞数据"导致接口契约漂移。

为什么 Day 5/6 也用 Pydantic

Day 5 的 `extract` 返回用 Pydantic 字段校验（score 是 `int` 还是 `None`）。Day 1 的 `HealthResponse` 是同一个思路：**模型既是文档（自动进 OpenAPI），又是运行时校验器**。

与"人类复核"的联系

Day 5 的核心是"模型抽、程序核、人拍板"。FastAPI 这里把"程序核"提前到**接口层**：连返回字段的形状都不对，根本出不了门（`extra="forbid"` 直接 422/500）。这是把校验前移的工程习惯。

关联

- [[../Day1 知识库|Day1 知识库]]
- [[Swagger 与 OpenAPI 自动文档]]

 Swagger 与 OpenAPI 自动文档

两个自动端点

| 路径 | 是什么 | 谁用 |
|---|---|---|
| `GET /docs` | Swagger UI，浏览器里可点的交互文档 | 人（开发、联调） |
| `GET /openapi.json` | OpenAPI 契约（机器可读 JSON） | 代码生成、测试、第三方对接 |

FastAPI 根据你写的路由、Pydantic 模型**自动生成**这两样，不用手写文档。

改元数据它们会跟着变

`FastAPI(...)` 构造时的参数会写进 `info` 对象：

```python
app = FastAPI(
    title="专利业务教学 API",
    summary="专利业务教学 API 的最小可用版本，仅用于实习演示。",
    version="0.1.0",
    description="只处理虚构教学数据……",
    contact={"name": "实习教学助手", "email": "student@example.com"},
)
```

挑战任务加上 `summary` 和 `contact` 后，重新看 `/openapi.json` 的 `info`：

```json
{
  "title": "专利业务教学 API",
  "summary": "专利业务教学 API 的最小可用版本，仅用于实习演示。",
  "version": "0.1.0",
  "contact": {"name": "实习教学助手", "email": "student@example.com"}
}
```

`/docs` 页面顶部也会显示这些文字。

安全提醒（Day 5 学的延续）

Swagger UI 只用于**本机教学**。生产环境不该把接口文档公开给外人——和"Key 只走环境变量、不进 Git"是同一类纪律。

关联

- [[../Day1 知识库|Day1 知识库]]
- [[Pydantic 响应模型与 strict]]
TestClient 为什么不需要真实端口

现象

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_returns_version():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
```

运行 `pytest` 时**没有先启动 `fastapi dev`**，但测试照样通过。为什么？

原因

`TestClient` 在**当前 Python 进程内**直接调用 FastAPI 应用对象（`app`），绕过网络栈：

```
普通访问：客户端 → 网络(127.0.0.1:8000) → Uvicorn → app
TestClient： 测试代码 → app（同一进程，无端口、无 socket）
```

它底层用 `httpx2` 直接把请求交给 ASGI app，所以：
- 不需要监听 8000 端口（不会和正在跑的 dev 服务抢端口）；
- 不访问互联网；
- 启动快、可并行、CI 里稳定。

什么时候才需要真端口

只有"手动验证"或"端到端联调"时才启动 `fastapi dev` / `uvicorn` 然后用浏览器/`curl` 打。自动化测试一律用 TestClient。

关联

- [[../Day1 知识库|Day1 知识库]]
- [[HTTP 与 ASGI 数据流]]
