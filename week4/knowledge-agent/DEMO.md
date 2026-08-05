# 演示稿（Day 21）

面向答辩的现场演示顺序，所有输出均来自本机真实运行。预计 10–15 分钟，超时则保留「正常问答 / 拒答 / 工具」三项。

环境：DeepSeek OpenAI 兼容 API，`DEEPSEEK_MODEL=deepseek-v4-flash`，依赖仅 `openai`。

## 1. 用户、问题和明确非目标（1 分钟）

- **用户**：需要基于内部脱敏资料提问的人（如专利审查员）。
- **问题**：针对 `knowledge/` 下三份资料（llm.md / agent.md / mcp-security.md）的自然语言提问。
- **明确非目标**（也是所有"为什么没做 X"的回答基准）：不联网、不做长期记忆、不做多用户、不做网页界面、不用向量库、不做生产部署。

## 2. 加载—检索—上下文—模型—来源 数据流（2 分钟）

一条问题走过的路径：

```console
python retriever.py "为什么不能只靠提示词保证安全？"
```

实际输出（节选）：

```json
[
  {
    "source": "mcp-security.md",
    "chunk": 1,
    "text": "# MCP 与安全\n\nMCP 让 Client 使用统一协议发现和调用 Server 提供的 Tools、Resources 与 Prompts。MCP 负责连接规范，不会自动保证工具安全。\n\n提示注入可能诱导 Agent 忽略规则或越权操作。防护应落在权限隔离、工具白名单、参数校验、人工确认和调用上限等程序边界，不能只依赖提示词。",
    "score": 0.4615
  }
]
```

要点：检索是关键词评分（可解释、可单测、零依赖），来源由程序从检索结果取文件名集合，`agent.py` 只负责按上下文组织语言，不编造来源。

## 3. 正常问答、拒答和计算器（4 分钟）

```console
python agent.py "Agent 的基本组成有哪些？"
```

```text
根据提供的上下文，Agent 的基本组成包括**目标、上下文、工具、状态、观察和停止条件**。

来源：agent.md
[usage] total=418
```

```console
python agent.py "本校图书馆周日几点闭馆？"
```

```text
资料不足，无法回答。
[usage] total=0
```

拒答发生在调用模型之前（`answer()` 在检索为空且非算术时直接返回），所以 `total=0`，既防幻觉又省费用。

```console
python agent.py "请计算 (18+6)/3"
```

```text
[tool round=1] calculate: 8.0
(18+6)/3 = 8
[usage] total=768
```

## 4. 测试集、关键指标和一次优化（2 分钟）

- 离线测试：`python -m unittest discover -v` → **30 tests OK**（Day18 的 10 + Day19 的 6 + Day17 的 14）。
- 批量评测：`python eval.py test_questions.json` → **10/10 passed**，`source_hit=100%`、`keyword_hit=100%`、`refusal_correct=100%`，总 Token 3675（2 道拒答题 `total=0`，离线通过）。脱敏报告见 `EVAL_SUMMARY.md`。
- 一次优化（挑战任务）：关键词 → Embedding 检索，只改 `retriever.py` 内部 `search`，`agent.py` 不动；用同一份 `test_questions.json` 跑 before/after 对比，重点看近义问是否被补召回。

## 5. 安全边界、已知限制和下一步（1 分钟）

**安全边界（分层）**

- 无检索结果 → 在 API 调用前拒答（不建 client、不消耗 Token）。
- 计算器只接受数字、括号和 `+ - * /`；工具名白名单 + 参数校验 + 最多 3 轮 / 3 次。
- 日志（`agent.log`）只记时间、工具名、成功状态，无 Key、无问题全文。
- 白名单在代码层挡攻击的证据：单测 `tests.test_tools_agent.ToolAndAgentTests.test_calculator_rejects_code` 通过（`ast` 解析到 `__import__` 这类调用直接拒绝）。

**两个真实安全演示（注意区分两层）**

- 输入 `请计算 __import__('os').system('whoami')`（无数字）：`looks_like_calculation` 不匹配 → 归为知识问题 → 检索不到 → 拒答，`total=0`。防线在「无上下文不答」。
- 输入 `请计算 1+1; __import__('os').system('whoami')`（带数字）：进计算器，模型只把 `1+1` 交给工具，危险部分不执行；即便模型真把整串交给 `calculate`，`ast` 白名单也会拒绝。

**已知限制**

- 关键词检索不识同义/近义；自动关键词评分 ≠ 人工事实核查；仅适用于小型本地资料；无联网、无多用户、无并发。

**下一步**：只加 Embedding 检索，before/after 验证，单项掉就回退，不在答辩前临时改架构。

## 故障预案

- 网络失败：先展示离线测试（`unittest`）与检索结果（`retriever.py`）。
- API 不可用 / 余额不足：展示脱敏评测摘要（`EVAL_SUMMARY.md`）与已保存的拒答证据（`total=0`）。
- 缺少 Key：临时 `Remove-Item Env:DEEPSEEK_API_KEY`（PowerShell）后运行会报中文「未设置 DEEPSEEK_API_KEY」、退出码非 0，不泄漏堆栈；恢复 Key 即恢复。
- 任何情况下不临时更换未知密钥。
