# EVAL_SUMMARY（Day20 批量评测，关键词检索基线 before）

> 评测对象：week4/knowledge-agent 当前实现（retriever.py 关键词检索 + agent.py 问答）。
> 指标含义见 Day20 最小理论；本报告是**关键词检索基线（before）**，挑战任务 Embedding 检索为 after。

## 汇总

- 题目数：10（8 答 + 2 拒）
- 通过率 passed（source_hit ∧ keyword_hit ∧ refusal_correct）：100%
- 来源命中率 source_hit：100%
- 关键词命中率 keyword_hit：100%
- 拒答正确率 refusal_correct：100%
- 总 Token：3675（工程成本，与正确性分开看）

## 逐题明细

| # | 难度 | 问题 | passed | 来源 | 来源命中 | 关键词命中 | 拒答正确 | total |
|---|---|---|---|---|---|---|---|---|
| 1 | easy | Token 是什么？ | Y | llm.md | Y | Y | Y | 414 |
| 2 | easy | 什么是上下文窗口？ | Y | agent.md, llm.md | Y | Y | Y | 487 |
| 3 | easy | 什么是大模型幻觉？ | Y | llm.md | Y | Y | Y | 424 |
| 4 | medium | Agent 的基本组成有哪些？ | Y | agent.md | Y | Y | Y | 416 |
| 5 | medium | 谁真正执行模型提出的工具调用？ | Y | agent.md | Y | Y | Y | 417 |
| 6 | hard | 工具调用需要哪些安全措施？ | Y | agent.md, mcp-security.md | Y | Y | Y | 579 |
| 7 | easy | MCP 中 Client 和 Server 是什么关系？ | Y | mcp-security.md | Y | Y | Y | 439 |
| 8 | medium | 为什么不能只靠提示词保证安全？ | Y | mcp-security.md | Y | Y | Y | 499 |
| 9 | easy | 本校图书馆周日几点闭馆？ | Y | — | Y | Y | Y | 0 |
| 10 | medium | 请介绍量子芯片的最新型号。 | Y | — | Y | Y | Y | 0 |

## 说明

- 来源命中率与关键词命中率是自动代理指标，不等于语义正确率；原回答已完整保留在 eval_results.json，需要人工抽查关键概念是否真正成立。
- 拒答正确率只看检索不到且非算术时是否拒答，不依赖模型，可离线验证（本题 2 道拒答题已离线通过）。
- 本份为关键词检索基线 before；挑战任务 Embedding 检索为 after，用同一份 test_questions.json 跑 before/after 对比，重点看近义问召回是否被补上。
