# FastAPI Day 2 知识库（MOC）

> 第二天解决一件事：怎么让客户端把数据"交进来"，服务端算完再把结构化结果"交回去"。

## 今天搞懂的主线

1. **POST 把数据交进来**：Day 1 只有 `GET /health`（读固定值），Day 2 是 `POST /api/v1/fees/summary`，客户端在请求体里发 JSON，服务端解析后再算。详见 [[请求模型与 POST 请求体]]。
2. **请求模型与响应模型分工**：请求模型（`FeeSummaryRequest`）负责把客户端 JSON 解析成 Python 对象；响应模型（`FeeSummaryResponse`）负责约束返回形状。两者都用 Pydantic，但严格度不同。详见 [[响应模型与 strict 复用]]。
3. **复用已有业务逻辑，不重写**：Day 6 的 `fee_calc.calculate` 是纯函数，直接 import 进来当"算账内核"，`main.py` 只做 HTTP 适配。详见 [[把 CLI 计算逻辑包成 API]]。

## 与 Day 1 的联系

- Day 1 的 `HealthResponse` 用了 `strict=True` + `extra="forbid"`，Day 2 的响应模型延续同一套约束，只是字段更多、还有嵌套的 `dict[str, str]`。
- Day 1 用 `GET` 读、Day 2 用 `POST` 提交，正好把"方法代表意图"那张表补全（Day 1 的 HTTP 名词表里 `POST` 就是"提交数据"）。

## 原子笔记索引

- [[请求模型与 POST 请求体]]
- [[响应模型与 strict 复用]]
- [[把 CLI 计算逻辑包成 API]]

## 回到

- [[Day1 知识库]]
