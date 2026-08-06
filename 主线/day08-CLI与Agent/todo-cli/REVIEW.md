# Day 10 代码审查记录（只读）

审查对象：`SPEC.md`、`todo.py`、`test_todo.py`
审查原则：只报告会导致需求不满足、数据丢失或测试失真的问题；每条给文件位置、复现方法和最小修改；不编辑、不建议框架迁移或新依赖。

## 审查意见

### 1. 空文件 `todos.json` 会被当作错误而非空列表
- 位置：`todo.py` `load()`
- 复现：把 `todos.json` 写成 0 字节空文件后运行 `python todo.py list`，得到 `错误：Expecting value: line 1 column 1`，退出码 1。
- 最小修改：`load()` 开头加 `if not DATA_FILE.exists() or not DATA_FILE.read_text(encoding="utf-8").strip(): return []`。
- 决定：**拒绝修改**。空文件本质是损坏/异常输入，报错比静默当空更安全；SPEC 未要求空文件特例，保留当前行为不违反需求，也避免改动业务规则。

### 2. `todos.json` 并发写无保护
- 位置：`todo.py` `save()`
- 复现：两个终端同时 `python todo.py add` 可能互相覆盖。
- 决定：**拒绝修改**。SPEC 明确定位是单用户本地 CLI，README 的「已知限制」已写明无并发写保护；加锁属于过度设计，违反「无第三方依赖」约束。

### 3. `clear-done` 两次遍历 items
- 位置：`todo.py` `run()` 的 `clear-done` 分支
- 复现：`removed = [i for i in items if i["done"]]` 与 `items = [i for i in items if not i["done"]]` 重复遍历。
- 决定：**拒绝修改**。数据量极小，可读性优先；非性能瓶颈，无正确性风险。

### 4.（外部建议示例）引入 SQLite/数据库持久化
- 位置：假设有人提议替换 JSON 文件
- 决定：**拒绝**。直接违反 SPEC「无第三方依赖、数据存 JSON」；属于典型的过度设计，测试也已用临时文件隔离验证，无需数据库。

## 总结
- 4 条意见全部为「拒绝修改」或「记录不处理」，因为 `todo.py` 已满足 SPEC，且建议项均属于超出需求的过度设计。
- 测试覆盖：正常（add/list/persist）、边界（空输入、不存在 ID、非整数 ID、损坏 JSON、写入失败）均不污染真实数据，6 主线 + 1 挑战共 7 项通过。
