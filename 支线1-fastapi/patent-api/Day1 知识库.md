# FastAPI Day 1 知识库（MOC）

> 第一天只解决一件事：HTTP 服务怎么跑起来、怎么被访问、怎么被测试。

## 今天搞懂的主线

1. **一次 HTTP 请求怎么走**：客户端 → `127.0.0.1:8000` → Uvicorn → FastAPI 路由函数 → 返回 JSON。详见 [[HTTP 与 ASGI 数据流]]。
2. **响应用 Pydantic 模型约束**：`HealthResponse` 用 `strict=True` + `extra="forbid"`，保证返回字段类型严格、不多不少。详见 [[Pydantic 响应模型与 strict]]。
3. **测试不需要真端口**：`TestClient` 在当前进程内直接调应用，不监听 8000，也不联网。详见 [[TestClient 为什么不需要真实端口]]。
4. **文档是自动生成的**：`/docs`（Swagger UI）和 `/openapi.json`（OpenAPI 契约）FastAPI 自动产出，改 `summary`/`contact` 元数据它们自动变。详见 [[Swagger 与 OpenAPI 自动文档]]。

## 与之前天的联系

- Day 5 / Day 6 都是**命令行程序**（CLI）：你手动跑 `python xxx.py`。FastAPI 把它们升级成**网络服务**：别人用 HTTP 调你。
- Day 6 学的"业务规则只留一份"在 FastAPI 里延续：`main.py` 只做 HTTP 适配，真正的算账/抽字段逻辑仍在 Day 5/6 的领域函数里。

## 原子笔记索引

- [[HTTP 与 ASGI 数据流]]
- [[Pydantic 响应模型与 strict]]
- [[TestClient 为什么不需要真实端口]]
- [[Swagger 与 OpenAPI 自动文档]]

## 回到

- [[../第一周周总结|第一周周总结]]
