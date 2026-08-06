# Agent Backend Day 10：空库复现、备份恢复、发布与答辩

## 今天做了什么

冻结功能，只做可复现交付：更新 `v0.2.0`、创建一键验收脚本、从新克隆与空数据库复现、用 `pg_dump` 做临时恢复、完成最终检查并准备 12 分钟演示。

> ⚠️ **可运行代码位置说明（重要）**
> 当天代码在培训 VM（Red Hat 8，`192.168.172.100`）真实跑通，是 `patent-agent-service`
> （Day 3 提交 `e13000b` 之上的演进）的一部分。**本仓库仅保留教材对应的设计与配置**，
> 未含 VM 实跑代码与输出，不伪造实跑日志。`evidence/` 与 `backups/` 不提交 Git。

## 关键技术点

- **「我机器能跑」不是交付**：最终验收从 Git 新克隆开始，不复用 `.venv`/`__pycache__`/未提交文件；数据库从空库 migration，checkpoint 由框架 setup，才能证明仓库含全部必要步骤。
- **migration、checkpoint setup、backup 是三件事**：migration 重建应用 Schema；checkpoint setup 重建 LangGraph 内部 Schema；`pg_dump/pg_restore` 恢复某时刻数据与两类 Schema；三者不可互相替代。
- **发布版本只在验收后打 tag**：先更新版本、提交、从新克隆验证、跑总验收，再创建 `v0.2.0` annotated tag；不在测试失败或工作区未提交时打 tag。

## 关键代码与配置

见同目录：

- `RELEASE_CHECKLIST.md`：安全 / 回归与契约 / 数据与恢复 / 异步 Agent / 发布 五节逐项确认清单。
- `ops/verify_agent_lab.sh`：从依赖（端口/容器）、migration、checkpoint setup、静态编译、离线+集成测试、起两 Worker 与 API、`/ready`、`/health` 版本、golden cases、证据安全扫描到最终 `verify_agent_lab: PASS` 的一键验收。只终止自己启动并记录 PID 的三个本地进程，不用 `pkill`，不删库/不 purge/不清 Redis。
- `version_bump.md`：Day 10 版本变更说明（`APP_VERSION` 0.1.0 → 0.2.0，仅改兼容断言）。

## 与教材对应章节

教材《大模型与智能体 Agent 工程与中间件两周实习教程》→ `## Agent Backend Day 10：空库复现、备份恢复、发布与答辩`（约第 6036–6624 行）。

## 结果或验证方式（在 VM 上执行）

1. `pytest` 旧 17 项 + 两领域模块 + `test_workflow.py` 通过；`/health` 版本 `0.2.0`。
2. 新克隆 + 空库：`alembic upgrade head` 与 `python ops/init_checkpoints.py` 成功，应用表与 checkpoint 表同时存在。
3. `pg_dump -Fc` → 恢复到唯一临时库 `agent_restore_<时间戳>`，应用行与 checkpoint thread 同时存在；删临时库（前缀守卫）。
4. `./ops/verify_agent_lab.sh` 最终输出 `verify_agent_lab: PASS`。
5. 仅当「新克隆/空库通过 + 临时恢复通过 + 一键验收通过 + checklist 每项有证据 + 工作区干净 + 无秘密/真实数据」同时满足，才 `git tag -a v0.2.0`。
6. 12 分钟答辩：目标/边界 → 三组件职责 → 创建幂等与 `202` → 图暂停不占 Worker → 重启后恢复 → Redis 降级 → Worker lost/重复投递 → golden/评测/安全 → 单机边界与下一步。

> 本仓库不保存上述输出；验证需在培训 VM 的 `patent-agent-service` 按教材步骤进行。
