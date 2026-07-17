# TestClient 为什么不需要真实端口

## 现象

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

## 原因

`TestClient` 在**当前 Python 进程内**直接调用 FastAPI 应用对象（`app`），绕过网络栈：

```
普通访问：客户端 → 网络(127.0.0.1:8000) → Uvicorn → app
TestClient： 测试代码 → app（同一进程，无端口、无 socket）
```

它底层用 `httpx2` 直接把请求交给 ASGI app，所以：
- 不需要监听 8000 端口（不会和正在跑的 dev 服务抢端口）；
- 不访问互联网；
- 启动快、可并行、CI 里稳定。

## 什么时候才需要真端口

只有"手动验证"或"端到端联调"时才启动 `fastapi dev` / `uvicorn` 然后用浏览器/`curl` 打。自动化测试一律用 TestClient。

## 关联

- [[../Day1 知识库|Day1 知识库]]
- [[HTTP 与 ASGI 数据流]]
