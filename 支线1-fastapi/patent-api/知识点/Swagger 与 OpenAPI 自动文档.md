# Swagger 与 OpenAPI 自动文档

## 两个自动端点

| 路径 | 是什么 | 谁用 |
|---|---|---|
| `GET /docs` | Swagger UI，浏览器里可点的交互文档 | 人（开发、联调） |
| `GET /openapi.json` | OpenAPI 契约（机器可读 JSON） | 代码生成、测试、第三方对接 |

FastAPI 根据你写的路由、Pydantic 模型**自动生成**这两样，不用手写文档。

## 改元数据它们会跟着变

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

## 安全提醒（Day 5 学的延续）

Swagger UI 只用于**本机教学**。生产环境不该把接口文档公开给外人——和"Key 只走环境变量、不进 Git"是同一类纪律。

## 关联

- [[../Day1 知识库|Day1 知识库]]
- [[Pydantic 响应模型与 strict]]
