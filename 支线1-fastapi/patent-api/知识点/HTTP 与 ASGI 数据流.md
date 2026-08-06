# HTTP 与 ASGI 数据流

## 一句话

客户端发 HTTP 请求，Uvicorn 负责监听端口并把请求交给 FastAPI 的路由函数，函数返回值再由 Uvicorn 包成 HTTP 响应送回客户端。

## 关键名词

| 名词 | 本日含义 | 本项目示例 |
|---|---|---|
| 客户端 | 发出 HTTP 请求的程序 | 浏览器、`curl`、TestClient |
| 服务端 | 接收请求并返回响应的程序 | FastAPI 应用 |
| 方法 | 请求意图 | `GET` 读取、`POST` 提交数据 |
| 路径 | URL 里定位接口的部分 | `/health` |
| 状态码 | 请求处理结果 | `200` 成功、`422` 请求不符合 Schema |
| ASGI | Python Web 应用与服务器的接口规范 | FastAPI 应用交给 Uvicorn 运行 |
| Uvicorn | 加载 ASGI 应用并监听端口的服务器 | `fastapi dev` 内部使用它 |

## 一次请求的最小过程

```
客户端 → 127.0.0.1:8000 → Uvicorn → FastAPI 路由函数
客户端 ← 状态码 + JSON ← Uvicorn ← 路由函数返回值
```

- `127.0.0.1` 只指向**当前这台电脑**（本机回环），外网访问不到，开发安全。
- `8000` 是端口，用来区分同一台电脑上的不同网络程序。
- `main:app` 里 `main` 是文件名 `main.py`，`app` 是文件里的 `app = FastAPI(...)` 对象。

## 为什么是 `async def` 还是 `def`

本日 `health()` 用普通 `def`，因为它只在内存里构造一个小对象、没有 `await` 的异步操作。不要为了"看着现代"机械改成 `async def`。

## 关联

- [[../Day1 知识库|Day1 知识库]]
- [[TestClient 为什么不需要真实端口]]
