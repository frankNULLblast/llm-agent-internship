# v0.2.0 Release Checklist

## 安全

- [ ] 仅含虚构教学数据
- [ ] `.env`、密钥、连接串和 `evidence/` 未提交
- [ ] 日志不含 OCR、请求体、密码和异常连接串
- [ ] PostgreSQL、Redis、RabbitMQ、FastAPI 只绑定回环地址

## 回归与契约

- [ ] 原 FastAPI 17 项测试通过
- [ ] 两个领域模块原测试通过
- [ ] `202/404/409/422/503` 契约通过
- [ ] `/health` 为 `0.2.0`
- [ ] `/ready` 正确区分 required/degraded

## 数据与恢复

- [ ] 空库 Alembic upgrade 成功
- [ ] LangGraph checkpoint setup 成功
- [ ] `pg_dump` 已在临时数据库恢复验证
- [ ] Redis 清空/停机不丢业务结果

## 异步 Agent

- [ ] 两个 Worker，各 concurrency=1、prefetch=1
- [ ] 无 Celery result backend
- [ ] 等待人工时 Worker 已释放
- [ ] approve/reject 均从同一 checkpoint 恢复
- [ ] Worker lost 与重复投递只有一份终态
- [ ] 六条 golden cases 全部通过

## 发布

- [ ] 新克隆复现通过
- [ ] `ops/verify_agent_lab.sh` 通过
- [ ] 工作区干净
- [ ] 已确认当前提交满足创建 annotated tag `v0.2.0` 的全部前提
