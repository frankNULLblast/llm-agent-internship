# llm-agent-internship · 大模型应用工程实习作品集

本仓库是大模型应用工程实习的完整代码作品集，按 **一支主线 + 三条支线** 组织，与实习 Obsidian 笔记框架一一对应。

## 主线：知识库问答 Agent（大模型应用核心）

从协作、提示词、API 基础，到软件工程、Agent / 工具 / 安全，最终在 day17–21 完成一个可本地运行的「知识库问答 Agent」：把三份脱敏内部资料变成可问答助手，具备检索增强、来源引用、未知拒答、受控计算器（`ast` 白名单沙箱）等能力。

- `主线/day01-协作起步` … `主线/day16-安全测试`：前期基础（day01–16）
- `主线/知识库问答Agent/`：day17–21 的连续项目（需求 → 文档检索 `retriever.py` → 问答闭环 `agent.py` → 受控工具 `tools.py` → 批量评测 `eval.py`），含 `README.md` / `DEMO.md` / `EVAL_SUMMARY.md`

## 支线一：FastAPI（接口层）

把主线 Agent 包成 HTTP 接口，让网页 / 程序可调用。

- `支线1-fastapi/patent-api/`：day01–05 渐进构建的专利 API 项目（HTTP 服务 → 请求响应 → 复核分流 → 测试契约 → 发布复盘）

## 支线二：Linux 与容器（运行环境）

把应用部署到真实服务器，用容器隔离、K3s 编排。

- `支线2-linux/linux-day1-裸金属起步` … `linux-day5-中间件实战`：day01–05（day2 系统巡检已实跑，day4 含 K3s 部署真实证据）

## 支线三：Agent 工程与中间件（稳定性）

异步队列、数据持久化、幂等终态等后端基础设施。

- `支线3-agent工程与中间件/agent-day1-基线拓扑` … `agent-day10-发布交付`：day01–10
- ⚠️ `agent-day3-队列异步`（RabbitMQ + Celery）的可运行代码在培训 VM（`~/llm-agent-internship/agent-middleware-plus/patent-agent-service`，commit `e13000b`），本仓库仅保留教材对应的设计与配置。

## 如何本地运行主线项目

参见 `主线/知识库问答Agent/README.md`（环境、依赖、设 Key、运行、测试、评测）。

## 说明

本目录是重排后的统一结构。原按 `dayXX` 命名的分支（day17–day21 等）仍保留在 GitHub 提交历史中，未删除。
