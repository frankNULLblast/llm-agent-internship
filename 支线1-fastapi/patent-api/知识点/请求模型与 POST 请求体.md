# 请求模型与 POST 请求体

Day 2 第一次让客户端往服务端"塞数据"。之前 `GET /health` 是服务端自己返回固定值，客户端什么都不用带。

## POST 请求体长什么样

客户端发 `POST /api/v1/fees/summary`，JSON 放在请求体（body）里，不是 URL：

```json
{
  "records": [
    {"patent_application_number": "CN202310000001.1", "fee_type": "申请费", "amount_yuan": "100.00"},
    {"patent_application_number": "CN202310000001.1", "fee_type": "年费", "amount_yuan": "50.00"}
  ]
}
```

FastAPI 用一个 Pydantic 模型接收它：

```python
class FeeRecord(BaseModel):
    patent_application_number: str
    fee_type: str
    amount_yuan: str

class FeeSummaryRequest(BaseModel):
    records: list[FeeRecord]
```

`def summarize_fees(request: FeeSummaryRequest)` 里，FastAPI 自动把请求体 JSON 反序列化成这个对象，字段不对就直接 422，根本进不了函数体。

## 为什么 amount_yuan 用 str

Day 6 的 `calculate` 内部用 `parse_amount` 校验金额，它要求 `amount_yuan` 是"最多两位小数的十进制字符串"（比如 `"100.00"`），传数字会报错。所以请求模型里 `amount_yuan` 也声明成 `str`，客户端传 `"100.00"` 或 `100`（Pydantic 默认会把它 coerce 成字符串）都能接住，再原样交给 `calculate`。

如果这里用 `float`，看起来自然，但会和 Day 6 的校验逻辑对不上，要么改 `calculate`、要么自己做转换——都违背"业务规则只留一份"。直接用 `str` 最省事。

## GET 和 POST 这次凑齐了

| 方法 | 数据从哪来 | 本项目例子 |
|---|---|---|
| `GET` | 客户端不传 body，仅 URL/查询参数 | `GET /health` |
| `POST` | 客户端在请求体里发 JSON | `POST /api/v1/fees/summary` |

关联
- [[Day2 知识库]]
- [[响应模型与 strict 复用]]
- [[Day1 知识库]]
