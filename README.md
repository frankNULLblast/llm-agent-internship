# 中知经纬实习

一份面向「大模型应用 / AI Agent 工程化」的实习记录与作品集。四条学习线：主线是大模型与 Agent 的工程化落地，支线一是 FastAPI Web 服务，支线二是 Linux 基础设施，支线三是 Agent 工程与中间件（十天专题，把前三条线拧成一个能排队、能持久化、能人工复核、能故障恢复的 Agent 服务）。下面的内容既是给自己做的阶段总结，也按「能让老师或面试官一眼看懂含金量」的方式组织，对标外面一个正经 AI 应用项目的结构。

> 本文件是实习作品集的代码仓库门面，对应 Obsidian 笔记库 `中知经纬实习/README.md`。Obsidian 里还有讲稿、ppt、教程、资料清单等纯笔记内容，不在此代码仓库内（见下方「仓库里有什么 / 仓库外有什么」）。

## 实习简介：这段时间到底干了什么

实习围绕一个核心问题展开：怎么把一个大模型，从「在网页里聊两句」，变成「能稳定干活、能服务化、能部署上线」的工程系统。

- 主线（day1–day19）走完了一条完整的 AI 应用工程师成长路径：从第一次用 Python 调大模型 API，到写专利票据抽取与复核系统，再到定义 Agent 工具、接 MCP 协议、做 Agent 安全测试与阶段考核，用两个 Agent 平台做 A/B 实验，第四周转入知识库问答 Agent 的需求定义、检索基线与问答闭环。
- 支线一（FastAPI，5 天）把已有的业务逻辑包成 HTTP 服务：请求响应模型、状态码语义、测试契约、可复现发布。
- 支线二（Linux，5 天）从裸金属开始搭基础设施：装系统、配权限、跑容器、上 K3s、部署 MySQL 和 RabbitMQ 中间件。
- 支线三（Agent 工程与中间件，10 天）是前三条线的合流：把无状态的专利业务 API 改造成 LangGraph + PostgreSQL + Redis + RabbitMQ + Celery 的异步 Agent 服务，跑到人工复核那一步能停下来，人给了决定再从 checkpoint 恢复接着跑。

四条线不是各学各的，而是互相印证：底层环境不稳，上层 Agent 就跑不起来；不懂服务化，模型能力就出不了门。

## 能力提升：我在这过程中长进了什么

- 大模型应用开发：不再只会调聊天接口，能自己做结构化输出、异常兜底，能定义工具 Schema 让模型调用，能接 MCP 统一发现外部工具。
- 工程化素养：养成了「先写可验收需求（SPEC），再写代码，用测试当证据」的习惯；会做单元测试、代码审查、Git 最小修复、可复现发布。
- 后端服务：用 FastAPI + Pydantic 把业务逻辑包成服务，理解 200/400/422/500 各自代表谁的责任。
- 基础设施：能在 Linux 上从装系统一路做到容器化两副本部署，会配 SELinux、rootless 容器、K3s，会搭消息队列和数据库。
- 和 AI 编程工具协作的方法：明白「Agent 说做完了不是证据，diff 加测试才是」，懂得权限审批和先计划后实现。
- 知识管理：每天把和工具的对话沉淀成 Obsidian 双向链接笔记，形成可复用的知识点库，不再重复踩坑。

## 就业价值：这能写进简历、搬上面试的东西

对标外面一个 AI 应用工程师的入门项目，这段时间产出了三块能直接讲的作品：

1. 专利票据智能抽取与复核系统：模型负责抽取、程序负责校验、人工负责复核，职责边界清晰，还用 FastAPI 服务化。这是最像「真实业务项目」的一块。
2. 从裸金属到 K8s 的基础设施实践：完整走了一遍 VMware 装系统 → Podman → K3s → 中间件，能讲清楚「为什么不能一上来就上 K8s」。
3. Agent 工具链实践：Function Calling、自定义工具、MCP、Skills，知道这些分别解决什么问题、不在哪一层。

对应可投的方向：大模型应用工程师、AI Agent 开发、Python 后端、DevOps 入门、算法工程支持。面试时能讲的具体问题包括：模型抽取和程序校验为什么要分开、MCP 解决了什么、K8s 为什么要从裸系统一层层铺、怎么用最小修复定位一个 bug。

## 现在我能独立完成什么

- 独立用 Python 调大模型 API，做结构化 JSON 输出和四类异常兜底。
- 独立写一个带 SPEC 和测试的 CLI 工具，用 JSON 持久化数据。
- 用 FastAPI 把已有业务逻辑包成 HTTP 服务，写好测试契约并打版本发布。
- 在 Linux 上从装系统到部署容器化两副本服务，并搭起 MySQL + RabbitMQ 中间件。
- 定义一个 Agent 工具或接上 MCP，用两个平台做 A/B 实验对比效果。

## 为什么过程重要：这些步骤不能省

这几条是我踩过之后才真正信了的：

- 顺序不能跳。先写文档和测试样例，再写代码；先搭稳底层环境，上层 Agent 才稳。跳一步，后面全塌。
- 证据文化。Agent 报「完成」不算数，git diff 加测试通过才算。每一步都要有可检查的证据。
- 知识要沉淀。每天的交互变成可复用笔记，下次遇到同类问题直接调出来，而不是重新摸索。
- 过程本身就是项目。外面公司的 AI 应用岗，日常就是这些：写需求、调模型、包服务、搭环境、做实验。把过程记清楚，它就是一份拿得出手的项目经历。

## 内容结构：学习路线与资料导航（本代码仓库）

本仓库按 **一支主线 + 三条支线** 组织，与 Obsidian 笔记框架一一对应。仓库里只有代码与项目交付物，笔记原文在 Obsidian 库。

### 主线 · 大模型与 Agent 工程化（day1–day21）

- `主线/day01-协作起步` … `主线/day16-安全测试`：前期基础（day01–16）
- `主线/知识库问答Agent/`：day17–21 的连续项目（需求 → 文档检索 `retriever.py` → 问答闭环 `agent.py` → 受控工具 `tools.py` → 批量评测 `eval.py`），含 `README.md` / `DEMO.md` / `EVAL_SUMMARY.md`
- 每日知识库与实习日志见 Obsidian `实习内容/主线/`

| 天              | 当天研究的内容                              |
| -------------- | ------------------------------------ |
| day1 协作起步      | 和 AI 工具协作的方法，把每天交互沉淀成可复用知识点          |
| day2 提示词实验     | 提示词的输入、输出、模型、时间的系统实验记录               |
| day3 模型对比      | 多个大模型横向对比，看各自长短                      |
| day4 API初探     | 第一次用 Python 直接调大模型 API，做结构化输出与异常兜底   |
| day5 票据抽取      | 专利票据识别 Demo：模型抽取 + 程序校验 + 人工复核       |
| day6 软件开发      | 走完软件开发全过程，做出可复现发布的费用计算 CLI           |
| day7 AI协作纪律    | 怎么正确跟 Codex / WorkBuddy 这类 AI 编程工具协作 |
| day8 CLI与Agent | 可验收需求驱动的编码 Agent 协作，JSON 持久化待办 CLI   |
| day9 调试与Git    | Git 调试流程与最小修复，单一根因、回归验证              |
| day10 测试与审查    | 单元测试、只读代码审查、写可复现 README              |
| day11 关键词统计    | 阶段挑战：Markdown 关键词统计器                 |
| day12 Agent入门  | 从聊天模型到 Agent，理解目标—工具—观察—停止的循环        |
| day13 函数调用     | Function Calling 与自定义工具，安全校验与调用控制    |
| day14 MCP协议    | MCP 与 Skills 基础，统一发现和调用外部工具          |
| day15 Agent对比  | 用两个 Agent 平台对专利票据流程做 A/B 实验          |
| day16 安全测试与考核 | Agent 安全测试（提示注入/工具白名单/轮数上限）、阶段小测、第三周工具对比总结 |
| day17 需求数据与骨架 | 第四周开篇：知识库问答 Agent 的需求、三份脱敏资料、10 条验收问题与项目骨架 |
| day18 文档加载切分与关键词检索 | 纯标准库检索器：加载/切分/关键词检索，10 测试通过，固定问题验证命中与拒答 |
| day19 问答引用拒答与受控工具 | agent.py 问答闭环+来源+拒答，tools.py 受控计算器，离线测试 OK，在线三场景验证（commit 15a871e） |
| day20 批量评测与答案评估 | eval.py 在 10 条验收问题跑当前实现，source_hit/keyword_hit/refusal_correct 三项，10/10 passed |
| day21 最终答辩与复盘 | 答辩题库答案、六阶段证据表、DEMO 稿、最终复盘、挑战任务 Embedding 检索（见 `主线/知识库问答Agent/`） |

### 支线1-fastapi · FastAPI Web 服务（fastapi-day1–day5）

把主线 Agent 包成 HTTP 接口，让网页 / 程序可调用。

- `支线1-fastapi/patent-api/`：day01–05 渐进构建的专利 API 项目（HTTP 服务 → 请求响应 → 复核分流 → 测试契约 → 发布复盘）
- 每日知识库与实习日志见 Obsidian `实习内容/支线1-fastapi/`

| 天 | 当天研究的内容 |
| --- | --- |
| fastapi-day1 HTTP服务 | HTTP 请求怎么走、响应模型怎么约束、测试为什么不需要真端口 |
| fastapi-day2 请求响应 | POST 把数据交进来，请求模型与响应模型分工，复用已有计算内核 |
| fastapi-day3 复核分流 | 票据复核与分流，状态码表达责任归属（400/422/500） |
| fastapi-day4 测试契约 | 接口测试、契约与调试，定位请求层 / 领域层 / 响应层问题 |
| fastapi-day5 发布复盘 | 集成、发布与复盘，固定依赖、写 README、打版本标签、新克隆验证 |

### 支线2-linux · Linux 基础设施（linux-day1–day5）

把应用部署到真实服务器，用容器隔离、K3s 编排。

- `支线2-linux/linux-day1-裸金属起步` … `linux-day5-中间件实战`：day01–05（day2 系统巡检已实跑，day4 含 K3s 部署真实证据）
- 每日知识库与实习日志见 Obsidian `实习内容/支线2-linux/`

| 天                | 当天研究的内容                                     |
| ---------------- | ------------------------------------------- |
| linux-day1 裸金属起步 | VMware + 龙蜥 Anolis 安装、首次登录、SSH 打通、打快照       |
| linux-day2 系统巡检  | 命令行、文件系统、权限、进程服务、SELinux 与系统巡检              |
| linux-day3 容器入门  | 网络排错 + rootless Podman，构建 Nginx 镜像跑容器       |
| linux-day4 K3s部署 | 单节点 K3s，把镜像部署成两副本服务                         |
| linux-day5 中间件实战 | MySQL + RabbitMQ：生产者 → 队列 → 消费者写库 → 提交后 ACK |

### 支线3-agent工程与中间件 · Agent 工程与中间件（agent-day1–day10）

十天专题，贯穿项目是一个虚构专利业务 Agent 服务。前三条线学的东西在这里合流：FastAPI 提供接口层，Linux 提供 rootless Podman 底座，主线的票据抽取与费用计算作为 Agent 图里的确定性节点。

- `支线3-agent工程与中间件/agent-day1-基线拓扑` … `agent-day10-发布交付`：day01–10
- ⚠️ `agent-day3-队列异步`（RabbitMQ + Celery）等可运行代码在培训 VM（`~/llm-agent-internship/agent-middleware-plus/patent-agent-service`，commit `e13000b`），本仓库保留教材对应的设计与配置骨架。
- 每日知识库与实习日志见 Obsidian `实习内容/支线3-agent工程与中间件/`

| 天 | 当天研究的内容 |
| --- | --- |
| agent-day1 基线拓扑 | rootless Podman 起 PostgreSQL / Redis / RabbitMQ，全部只绑回环，固定依赖与镜像版本 |
| agent-day2 数据持久化 | SQLAlchemy 建任务表、Alembic 可回退迁移，任务状态有唯一事实源 |
| agent-day3 队列异步 ✅ | RabbitMQ + 单队列 Celery，把执行从 HTTP 请求里搬出去（commit e13000b） |
| agent-day4 幂等终态 | 双 Worker、late ACK、终态守卫与行锁，至少一次不等于恰好一次 |
| agent-day5 Web中间件 | request_id 中间件、202 异步接口、Idempotency-Key 幂等创建、/ready 依赖分级 |
| agent-day6 缓存降级 | Redis 只缓存不可变终态，cache-aside 读写顺序，Redis 挂了自动回源 |
| agent-day7 LangGraph | 固定五节点图，模型只负责结构化抽取，领域函数管规则 |
| agent-day8 状态检查点 | PostgreSQL checkpoint + interrupt 暂停，人工复核后恢复同一个 run_id |
| agent-day9 可观测性 | 三种 ID 串成证据链、六条 Golden Cases、故障矩阵与恢复判据 |
| agent-day10 发布交付 | 空库复现、备份恢复演练、v0.2.0 发布与答辩 |

当前状态：agent-day1 ✅ / day2 ✅ / day3 ✅ 已实跑完成（commit 63d9170 / d2803a8 / e13000b，分支 agent-middleware-plus）；day4–day10 仍为预习骨架。

### 仓库外有什么（在 Obsidian 笔记库，不在本仓库）

- **讲稿**：各周向老师汇报的口播稿与文字材料（第一周、第二周、第三周汇报讲稿）。
- **ppt**：用 cyberppt / pptmaster 生成的三周汇报幻灯片（.pptx）。
- **教程**：老师发的原始教程与教材（大模型与智能体系列教程，含 Linux / FastAPI / Agent 工程与中间件三个方向的 plus 版）。
- **资料清单**：实习导出与交接清单（带走哪些数据、怎么带走）。

## 如何本地运行主线项目

参见 `主线/知识库问答Agent/README.md`（环境、依赖、设 Key、运行、测试、评测）。

## 说明

本目录是重排后的统一结构（分支 `restructure`）。原按 `dayXX` 命名的分支（day17–day21 等）仍保留在 GitHub 提交历史中，未删除。
