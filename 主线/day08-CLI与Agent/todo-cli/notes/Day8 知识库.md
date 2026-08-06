# Day 8 知识库（MOC）

本日主题：**可验收需求 → 编码 Agent 协作 → JSON 持久化 CLI**。

## 一、核心知识点
- [[知识点/可验收需求与 SPEC]]：为什么"做个待办程序"不是需求，四条命令 + 验收命令才是
- [[知识点/持久化与 JSON]]：关闭程序后数据还在，靠标准库 json + Path 落盘
- [[知识点/Agent 协作纪律：先计划后实现]]：拆任务、列验证命令、git diff 即证据
- [[知识点/clear-done 挑战]]：加命令前先改 SPEC，再写代码

## 二、交付物
- 练习仓库：`llm-agent-internship/week2/day08/todo-cli/`（SPEC.md + todo.py + .gitignore）
- 验收：固定命令序列对照预期输出全绿；错误走 stderr、退出码非 0
- 推送分支：`day08`

## 三、与前后章的关系
- 前：[[Day7 知识库]]（怎么跟 Codex/WorkBuddy 协作，本次直接拿 WorkBuddy 当 Agent）
- 后：Day 9（Git、调试与最小修复，会在本 todo-cli 之外另起 bug-lab）、Day 10（给本 CLI 写单测 + README）

## 四、当日模糊需求改写
"做一个待办程序" → SPEC.md 四条命令各自定义输入/输出/错误/退出码，数据持久化到 todos.json；验收用固定序列对照预期输出。详见 [[Day8 实习日志 Better than before]]。
