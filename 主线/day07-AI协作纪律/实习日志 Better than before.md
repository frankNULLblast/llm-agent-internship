# 实习日志 Better than before · Day 7

日期：2026-07-20
方向：大模型与智能体应用
主题：Codex、腾讯 WorkBuddy 与正确协作方式

## 今日目标

在同一个安全练习仓库里分别用 Codex 和 WorkBuddy 完成同一个小改动（让 `greet` 对空白姓名抛出 `ValueError` 并加测试），对比两者在计划、审批、结果上的差异，并把任务映射到软件开发六阶段。

预计耗时：装环境 1h + 理论演示 1.5h + 两工具实验 3h + 复盘 1h。

## 前置与准备

- Codex CLI 已装（codex-cli 0.144.1）；腾讯 WorkBuddy 就是当前所在环境。
- 新建安全仓库 `llm-agent-internship/week2/day07/agent-lab`，写 `greet.py` / `test_greet.py`，跑通基线 `unittest` 并提交。
- 从基线 clone 出 `agent-lab-2`，两目录起点完全一致。
- 两个工具都只授权当天练习目录，不碰含真实数据的仓库（延续 Day4/5 的安全习惯）。

## 实验一：WorkBuddy（agent-lab-2）

发给 WorkBuddy 的提示词（与 Codex 完全一致）：

> 读取当前目录。目标：让 greet 对空白姓名抛出 ValueError，并增加对应 unittest。边界：只允许修改 greet.py 和 test_greet.py；不要安装依赖；不要执行高风险命令。先说明现状、修改计划和验证命令，等我确认后再编辑。

计划：在 `greet.py` 开头加 `if not name.strip(): raise ValueError("姓名不能为空白")`；`test_greet.py` 新增 `test_blank_raises` 断言 `greet("   ")` 抛 `ValueError`。验证用 `python -m unittest -v` + `git diff`。

审批：确认计划合理，批准执行。

结果：改动落地，`git diff` 仅触及 `greet.py` / `test_greet.py`；`python -m unittest -v` 显示 2 个测试 OK。diff 见 [[附件/workbuddy_diff]]。

## 实验二：Codex（agent-lab）

同一提示词发往 Codex。实际情况：Codex 在本机没法自己跑起来，是两层限制叠加（详见 [[知识点/Codex 被 401 阻断]]）：

- 先试 `codex login --device-auth`：需要 OpenAI 账号，但本机环境注册/登录要求海外手机号、连 Google 登录也被地区/IP 拦截，OAuth 完不成。
- 再试把 Codex 后端换成 DeepSeek：本机 `DEEPSEEK_API_KEY` 已在环境变量里，但实测即使把 `provider.openai.base_url` 指到 `https://api.deepseek.com/v1`，Codex 仍连 `api.openai.com`（自定义 `base_url` 被忽略）；更根本的是 Codex 依赖 OpenAI 的 **Responses API**（`/v1/responses`），DeepSeek 只提供 Chat Completions API，没有该端点，所以后端换不成。

这是环境限制，不是代码问题。为了把对比做完，我按 Codex 文档化的工作流纪律（先计划 → 审批 → 改动 → 验证）由操作员代执行同一改动，`agent-lab` 得到与 `agent-lab-2` 完全相同的 diff 与测试结果。

## 工具对比

| 维度 | WorkBuddy | Codex |
|---|---|---|
| 计划质量 | 先读目录、给出现状 + 修改点 + 验证命令，结构清晰 | 设计上同样先计划；本次未跑成，无法实测 |
| 权限透明度 | 桌面端 Plan / 编程模式切换，默认权限，不自动开 Full Access | 终端 CLI，sandbox 默认 read-only，写文件 / 命令需逐次审批 |
| 修改范围 | 仅 `greet.py` / `test_greet.py`，未越界 | 同上（操作员代执行，未越界） |
| 验证证据 | `git diff` + `unittest` 输出可读 | 同上 |
| 最终判断 | 成功完成，可作范例 | 环境缺凭据未能实测；流程纪律一致 |

## 六阶段证据

| 阶段 | 本任务产生的证据 |
|---|---|
| 需求 | 提示词写明"空白姓名抛 ValueError + 加测试"，可验收 |
| 设计 | 计划说明加校验分支与新增测试方法 |
| 编码 | `greet.py` / `test_greet.py` 的 `git diff` |
| 集成 | 改动在同一仓库内自洽，无新依赖 |
| 测试 | `python -m unittest -v` 输出 2 tests, OK |
| 上线 | 练习仓库，无生产上线；以 commit 固化终态 |

## 需要人工审查的风险（≥3）

1. 校验用 `name.strip()` 会同时拒绝纯空白与空串，要确认业务上是否允许名字带前后空格被自动接受（本任务接受）。
2. 异常文案是中文"姓名不能为空白"，若调用方依赖英文异常信息会不匹配。
3. Agent 报告"完成"不等于真通过，必须人工跑 `git diff` 与测试核对，不能只看它说的。
4. Codex / WorkBuddy 若被授予 Full Access 或上级目录权限，可能误改范围外文件。

## 验收清单

- [x] 两个 Agent 收到完全相同的任务和边界
- [x] 执行前看过计划，执行后看过 `git diff`
- [x] 指出至少 3 个需要人工审查的风险
- [x] 测试通过且能解释每一行改动
- [x] 完成工具对比表

## 关联

- [[Day7 知识库]]
- [[知识点/协作六阶段]]
- [[知识点/Agent 权限与审批]]
- [[知识点/diff 即证据]]
- [[知识点/补全vs聊天vsAgent]]
- [[知识点/Codex 被 401 阻断]]
- 上一天：[[day6/实习日志 Better than before]]
