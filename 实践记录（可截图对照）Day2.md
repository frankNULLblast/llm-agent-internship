# 实践记录（可截图对照）— FastAPI Day 2

> 每个场景给「敲什么命令 + 预期看到什么」，照着跑就能截图当证据。
> 承接 Day 1 的 `/health` 与 `.venv`，本日新增 `POST /api/v1/fees/summary`。

## 场景 0：进入项目并激活统一 .venv

```powershell
Set-Location "$HOME\llm-agent-internship\fastapi-plus\patent-api"
..\..\.venv\Scripts\Activate.ps1
python --version
```

截图：命令行里 `(.venv)` 前缀 + Python 版本。

## 场景 1：pytest（Day 2 共 4 个用例）

```powershell
python -m pytest -q
```

截图：终端显示 `4 passed`（health 1 个 + Day 2 正常/非法申请号/空数组 3 个）。

## 场景 2：启动开发服务器

```powershell
python -m fastapi dev main.py --host 127.0.0.1
```

截图：`Uvicorn running on http://127.0.0.1:8000`（服务起来了的铁证）。

## 场景 3：命令行发一条合法 POST（应得 200）

新开终端（同样激活 .venv 并 cd 到项目）：

```powershell
$body = @{
  records = @(
    @{ patent_application_number = 'CN202400000001.2'; fee_type = '申请费'; amount_yuan = '150.00' }
    @{ patent_application_number = 'CN202400000001.2'; fee_type = '年费'; amount_yuan = '50.00' }
    @{ patent_application_number = 'CN202400000002.3'; fee_type = '申请费'; amount_yuan = '200.00' }
  )
} | ConvertTo-Json -Depth 3 -Compress

(Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/fees/summary" -Method Post -ContentType "application/json" -Body $body) | ConvertTo-Json
```

截图：返回 `200` 与汇总体：

```json
{"currency":"CNY","record_count":3,"by_application":{"CN202400000001.2":"200.00","CN202400000002.3":"200.00"},"by_fee_type":{"年费":"50.00","申请费":"350.00"},"total_yuan":"400.00"}
```

> 申请号格式是 12 位数字 + `.` + 一位（可带 `CN` 前缀），不符合会返 422。

## 场景 4：浏览器 / Swagger UI 验证 POST 端点

浏览器打开 `http://127.0.0.1:8000/docs` → 展开 `POST /api/v1/fees/summary` → Try it out → 在 Request body 贴上面那条合法 JSON → Execute → 看到 `200` 和响应体。

截图：Swagger UI 页面，已展开该 POST 端点且响应 `200`。

## 场景 5：非法输入应得 422

```powershell
$body = @{ records = @(@{ patent_application_number = 'X'; fee_type = '申请费'; amount_yuan = '10.00' }) } | ConvertTo-Json -Depth 3 -Compress
(Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/fees/summary" -Method Post -ContentType "application/json" -Body $body).StatusCode
```

截图：返回 `422`（印证"非法输入返 422 而非 500"）。

## 场景 6：OpenAPI 文档含新端点

先 `Ctrl+C` 停掉场景 2 的服务，再：

```powershell
python -c "from main import app; import json; print('/api/v1/fees/summary' in app.openapi()['paths'] and list(app.openapi()['paths']['/api/v1/fees/summary'].keys()))"
```

截图：输出 `True ['post']`（端点存在且方法为 post）。

## 场景 7：git 证据

```powershell
git branch
git log --oneline -3
```

截图：`* fastapi-day2` 分支 + 提交 `922eff2 FastAPI Day 2: 封装 Day6 calculate 为 POST /api/v1/fees/summary(...)`。

## 验收清单对照

| 验收项 | 对应场景 |
|---|---|
| pytest 4 passed | 场景 1 |
| 服务能起 + 三种验证 | 场景 2（服务）+ 场景 3（命令行）+ 场景 4（浏览器/Swagger）+ 场景 6（OpenAPI） |
| 正常请求 200、非法请求 422 | 场景 3 + 场景 5 |
| 业务逻辑只来自 Day 6 一处 | main.py 顶部 `from fee_calc import calculate`（看代码截图） |
| Git 分支已提交 | 场景 7 |
