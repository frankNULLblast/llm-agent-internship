# Pydantic 响应模型与 strict

## 今天用到的响应模型

```python
class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    status: Literal["ok"]
    version: str
```

`@app.get("/health", response_model=HealthResponse)` 让 FastAPI 在返回前**用这个模型校验并序列化**返回值。

## 两个配置的含义

- `strict=True`：**严格类型**。比如 `version` 必须是 `str`，你返回个数字 `0.1.0`（实际是字符串）没问题，但如果你返回 `int` 或类型不符，Pydantic 直接报错而不是默默转换。它逼你类型对齐。
- `extra="forbid"`：**禁止多余字段**。返回体里多一个字段就报错。防止"顺手多塞数据"导致接口契约漂移。

## 为什么 Day 5/6 也用 Pydantic

Day 5 的 `extract` 返回用 Pydantic 字段校验（score 是 `int` 还是 `None`）。Day 1 的 `HealthResponse` 是同一个思路：**模型既是文档（自动进 OpenAPI），又是运行时校验器**。

## 与"人类复核"的联系

Day 5 的核心是"模型抽、程序核、人拍板"。FastAPI 这里把"程序核"提前到**接口层**：连返回字段的形状都不对，根本出不了门（`extra="forbid"` 直接 422/500）。这是把校验前移的工程习惯。

## 关联

- [[../Day1 知识库|Day1 知识库]]
- [[Swagger 与 OpenAPI 自动文档]]
