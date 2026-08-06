# Day 1 每日总结

## 今日完成
- 安装并配置 Codex（OpenAI CLI）：`npm install -g @openai/codex`，版本 `codex-cli 0.144.1`
- 把 Node 目录加入**用户级 PATH**，解决独立 PowerShell 找不到 codex 的问题
- 在 `llm-agent-internship\week1\day01` **离线建好 Python venv**（复用 hermes 缓存的 Python 3.11.15），并装好 pip 24.0
- 验证 `hello.py` **独立运行、退出码 0**
- 在 `week1\day01` 用 `git init` 初始化仓库，并完成首次提交 `eb0df33`
- 清理**孤儿 git 代理**（`127.0.0.1:7890`，软件已卸载），让 git 直连 GitHub
- 通过 GitHub API 把 day1 提交推送到 `github.com/frankNULLblast/llm-agent-internship`
- 搞懂「训练 / 推理 / 幻觉 / 人负责验收」四个核心概念

## 我能解释的三个概念 
- 1. **训练 vs 推理**：训练是模型从数据中学出参数（本实习**不训练**大模型）；推理是把输入交给已训练好的模型得到输出（我们天天做）。
- 2. **幻觉**：大模型不是数据库，它按概率逐词生成内容，可能编造看似合理但虚假的事实，所以关键事实要人工核实。
- 3. **人负责验收**：Agent（Codex / WorkBuddy）可以执行任务，但结果、权限、风险仍由使用者负责（human-in-the-loop）。

## 实践证据 
- 文件/提交：`week1/day01/hello.py`、`eb0df33 chore: complete day 1 environment check`；GitHub 仓库 `frankNULLblast/llm-agent-internship`
- 运行命令：`node -v` / `npm -v` / `codex --version` / `git --version` / `python --version`（五个均显示版本号）；`python hello.py`（退出码 0）；`git push`
- 关键输出：五个环境命令均出号 node -v v22.23.1，npm -v 10.9.8，codex --version codex-cli 0.144.1，git --version git version 2.53.0.windows.2，python --version python 3.11.15；`hello.py` 输出 `LLM Agent Internship / Date / Environment: OK`；GitHub 上可见该提交与 `hello.py`

## 遇到的问题与解决过程
- 现象：`codex` 在独立 PowerShell 报「无法识别」
  - 原因：WorkBuddy 管理的 Node 目录没加进系统 PATH（仅 WorkBuddy 自带 shell 有）
  - 解决：把 `C:\Users\rog 16\.workbuddy\binaries\node\versions\22.22.2` 加入用户级 PATH，重开终端即生效
- 现象：`python --version` 报 "Python was not found"
  - 原因：系统 `python` 解析到 Windows 商店假桩；真实 Python 未进 PATH
  - 解决：把 WorkBuddy 自带 Python 3.13.14 目录加入用户级 PATH；项目运行时用 venv 内 3.11.15
- 现象：git 连不上 GitHub
  - 原因：git 全局代理指向 `127.0.0.1:7890`，但代理软件早已卸载（孤儿配置）
  - 解决：`git config --global --unset http.proxy` / `https.proxy`，git 恢复直连

## Agent 做了什么，我做了什么
- Agent（WorkBuddy）：装 Codex、配 PATH、离线建 venv / 装 pip、诊断并清除代理、通过 API 建仓库并推送 day1 提交、生成概念讲解与总结
- 我（方可）：注册 GitHub 账号（frankNULLblast）、登录、生成 PAT、在终端跑验证命令、验收结果、做关键决策

## 明日计划 
- `git fetch origin && git reset --hard origin/master` 对齐本地与远程提交（远程 SHA 与本地不同）
- 吊销 PAT、清理 Windows 凭据
- 开始 Day 2 任务；把 `DAY1_SUMMARY.md` 等也纳入版本管理
