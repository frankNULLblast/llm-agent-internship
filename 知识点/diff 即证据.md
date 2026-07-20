# diff 即证据

Agent 说"完成"不是证据，测试输出和 `git diff` 才是证据。

- 验证顺序：说明目标边界 → Agent 读和计划 → 人审核 → 小步执行 → 运行验证 → 看 `git diff`。
- 即使 Agent 声称测试通过，也要人工跑 `python -m unittest -v` 与 `git diff`。

关联：[[Day7 知识库]] [[Agent 权限与审批]]
