# Patent Business Teaching API

一个只处理虚构教学数据的本地 FastAPI 服务。它复用已有 Python 领域函数，提供专利费用汇总和结构化票据人工复核分流。

## 边界

- 不验证专利、票据或费用的真实、合法、有效状态。
- `standard_manual_review` 和 `priority_manual_review` 都需要人工复核。
- 不保存请求，不提供数据库、认证、前端或云部署。
- 只在本机 `127.0.0.1` 运行。
- 含 Day 4 挑战接口 `/api/v1/patent-bills/recognize`：用离线假提取器把 OCR 文本还原为结构化票据，**不调用真实模型**，测试全程离线。

## 环境

- Python 3.11
- Windows PowerShell 7 或 Linux Bash

## 安装（Windows PowerShell 7）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 安装（Linux Bash）

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 测试

```console
python -m py_compile main.py fee_calc.py patent_bill.py test_main.py
python -m pytest -q
```

主线版本应为 `17 passed`；包含在线识别挑战代码时应为 `20 passed`，测试仍不调用模型。

## 开发运行

```console
fastapi dev main.py --host 127.0.0.1
```

## 本地发布运行

```console
fastapi run main.py --host 127.0.0.1 --port 8000
```

按 `Ctrl+C` 停止服务。

## 接口

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/health` | 健康检查与版本 |
| POST | `/api/v1/fees/summary` | 汇总虚构专利费用 |
| POST | `/api/v1/patent-bills/review` | 对结构化票据执行人工复核分流 |
| POST | `/api/v1/patent-bills/recognize` | OCR 文本还原为结构化票据（Day 4 挑战，离线假提取器） |

自动文档：

- Swagger UI：`http://127.0.0.1:8000/docs`
- OpenAPI：`http://127.0.0.1:8000/openapi.json`

## 费用请求（Windows PowerShell 7）

```powershell
Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/api/v1/fees/summary" `
    -ContentType "application/json; charset=utf-8" `
    -InFile .\fees.json
```

## 费用请求（Linux Bash）

```bash
curl -sS \
  -X POST \
  -H 'Content-Type: application/json' \
  --data-binary @fees.json \
  http://127.0.0.1:8000/api/v1/fees/summary
```

固定总额应为 `"5600.50"`。

## 票据复核请求（Windows PowerShell 7）

```powershell
Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/api/v1/patent-bills/review" `
    -ContentType "application/json; charset=utf-8" `
    -InFile .\bill_record.json
```

## 票据复核请求（Linux Bash）

```bash
curl -sS \
  -X POST \
  -H 'Content-Type: application/json' \
  --data-binary @bill_record.json \
  http://127.0.0.1:8000/api/v1/patent-bills/review
```

## 状态码

- `200`：成功完成计算或复核分流。
- `400`：请求形状正确，但违反领域规则。
- `422`：字段、类型或 JSON Schema 不符合接口要求。
- `500`：未预料的服务端缺陷。

## 已知限制

- 只处理小型 JSON 请求，未做容量和性能测试。
- 服务无状态，重启不会丢记录，因为本来就不保存记录。
- 未实现 HTTPS、认证、授权、限流、监控和生产进程管理。
- 专利申请号只检查课程样例格式。
- 不得使用真实票据或真实财务、法律业务数据。
