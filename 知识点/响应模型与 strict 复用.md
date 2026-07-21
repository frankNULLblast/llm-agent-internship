# 响应模型与 strict 复用

Day 2 的返回比 Day 1 复杂：`calculate` 吐出一个 dict，里面有标量也有嵌套字典。用响应模型把它框住，思路和 Day 1 的 `HealthResponse` 完全一致。

## 响应模型

```python
class FeeSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    currency: str
    record_count: int
    by_application: dict[str, str]
    by_fee_type: dict[str, str]
    total_yuan: str
```

`@app.post(..., response_model=FeeSummaryResponse)` 让 FastAPI 在返回前用这个模型校验并序列化。

## 为什么还用 strict + forbid

Day 1 讲过：`strict=True` 逼类型对齐（比如 `record_count` 必须是 `int`，不能是碰巧长得像的数字串）；`extra="forbid"` 禁止返回体多塞字段。Day 2 这里更关键——`calculate` 返回的 `by_application` / `by_fee_type` 是 `{申请号: 金额字符串}` 这种嵌套 dict，一旦某个值类型不对（比如金额忘了 `format_money` 变成 `Decimal`），`strict` 会直接把它拦在接口外，而不是把脏数据放出去。

## 请求模型为什么没加 strict

请求模型（`FeeSummaryRequest` / `FeeRecord`）我没加 `strict`。原因：客户端可能图方便把 `amount_yuan` 传成数字 `100` 而不是字符串 `"100"`，Pydantic 默认会把它 coerce 成 `"100"` 再交给 `calculate`，体验更友好。严格校验交给 Day 6 的 `parse_amount` 去做，两边都别重复。

一句话：请求端宽松接、业务端严格验、响应端严格出。

关联
- [[Day2 知识库]]
- [[请求模型与 POST 请求体]]
- [[Day1 知识库]]
