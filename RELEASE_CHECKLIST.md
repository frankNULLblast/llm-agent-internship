# v0.1.0 本地发布检查表

## 版本与范围

- [x] 应用版本为 `0.1.0`
- [x] 主线有健康检查、费用汇总和票据复核三个接口
- [x] 挑战接口 `/api/v1/patent-bills/recognize` 保留，README 已注明且测试为离线假提取器
- [x] Git 工作区没有无关修改

## 依赖与安全

- [x] Python 3.11
- [x] `python -m pip check` 通过
- [x] `.env`、`.venv`、缓存和 API Key 未入库
- [x] 样例全部是虚构教学数据
- [x] 启动地址固定为 `127.0.0.1`

## 测试结果

- [x] `py_compile` 通过
- [x] Day 5 原有 5 项领域测试通过（`../../week1/day05/test_patent_bill.py`）
- [x] Day 6 原有 9 项领域测试通过（`../../software-process/day06/fee-calculator/test_fee_calc.py`）
- [x] FastAPI 测试 20 项通过（含 Day 4 挑战 3 项，`test_main.py`）
- [x] 固定费用总额为 `5600.50`
- [x] 完整票据进入标准人工复核
- [x] 低置信度和缺金额进入优先人工复核

实际日期：2026-07-24

实际 Python/FastAPI 版本：Python 3.11 / FastAPI 0.139.0 / httpx2 2.5.0 / openai 2.45.0 / pytest 9.1.1

实际 pytest 结果：20 passed

## 发布与验证

- [x] README 安装、测试和启动命令已逐行执行
- [x] 已创建本地标签 `v0.1.0`
- [x] 已在新克隆目录检出 `v0.1.0`
- [x] 新克隆目录重新安装后测试通过
- [x] `fastapi run` 启动成功
- [x] `/health`、`/docs` 和 `/openapi.json` 可访问
- [x] 服务已用 `Ctrl+C` 正常停止

## 已知限制与失败处理

- 无数据库、认证、HTTPS、限流、监控和云部署。
- 不处理真实专利、票据、财务或法律判断。
- 首次发布没有更早的稳定生产标签；验证失败时停止本地服务，不移动或复用 `v0.1.0`，修复后发布新的 `v0.1.1`。
- 新克隆目录只用于固定版本验证，不在其中继续编辑或提交。
