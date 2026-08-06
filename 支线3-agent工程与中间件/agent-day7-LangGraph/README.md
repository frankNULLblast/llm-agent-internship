# Agent Backend Day 7：LangGraph 固定工作流与模型节点

## 今天做了什么

先不接 Celery：用 `InMemorySaver` 把「模型抽取 → 原 `build_result()` → 原 `calculate()` → 人工 `interrupt/resume`」连成固定图。自动测试只用 fake extractor；真实模型只做一次受控 smoke test。

> ⚠️ **可运行代码位置说明（重要）**
> 当天代码在培训 VM（Red Hat 8，`192.168.172.100`）真实跑通，是 `patent-agent-service`
> （Day 3 提交 `e13000b` 之上的演进）的一部分。**本仓库仅保留教材对应的设计与配置**，
> 未含 VM 实跑代码与输出，不伪造实跑日志。

## 关键技术点

- **图负责控制流，领域函数负责规则**：`extract_bill → review_bill（build_result） → summarize_fees（calculate） → await_human_review → approved/rejected`。申请号、日期、置信度、金额小数等规则仍只有原两个领域模块知道；不在图节点中复制这些规则。
- **`interrupt()` 是持久化断点，不是 `input()`**：节点调用 `interrupt(payload)` 后本次图执行结束并返回中断信息。恢复时必须使用同一 checkpointer、同一 `thread_id`、传入 `Command(resume=value)`、从该节点重新执行。因此 `interrupt()` 之前不能放发邮件、扣款、写终态等不可重复副作用——人工节点在 `interrupt()` 前只构造可序列化展示数据。
- **票据记录和费用记录始终分开**：票据记录是模型抽取的固定 9 字段 dict；费用记录是固定 3 字段 dict 列表；人工审批放在 `human_review`，不污染任一领域输入。
- **固定图**：没有 planner、工具选择器、循环或多 Agent；`extractor` 参数是唯一测试 seam（生产传真实函数，测试传 fake）。

## 关键代码与配置

见同目录：

- `patent_bill_extract.py`：教材 Day 7 对 `patent_bill.py` 的扩展——`extract_with_usage()`（返回 `(record, usage)`），`extract()` 保持原契约（返回 dict），SDK `timeout=30.0, max_retries=0`。
- `workflow.py`：`build_graph(extractor, checkpointer)`，固定 DAG 与节点。使用 `version="v2"`。
- `tests/test_workflow.py`：fake extractor 覆盖 approve / reject / 坏模型输出 / 坏费用输入 / 非法 resume 值；并验证首次 `invoke` 确实停在 interrupt、恢复必须用同一 thread。

## 与教材对应章节

教材《大模型与智能体 Agent 工程与中间件两周实习教程》→ `## Agent Backend Day 7：LangGraph 固定工作流与模型节点`（约第 3931–4440 行）。

## 结果或验证方式（在 VM 上执行）

1. `python -m pytest -q test_workflow.py` 与 `python -m pytest -q -m 'not integration'` 离线通过（不访问网络/容器）。
2. 临时实验：换 `thread_id` resume 原中断应抛异常，不能完成原 run。
3. 仅一次真实模型 smoke：`extract_with_usage(text)` 输出固定 9 字段 + `usage`（model/token/耗时）；密钥不进入文件/日志/shell history；不输出或计算单价。

> 本仓库不保存上述输出；验证需在培训 VM 的 `patent-agent-service` 按教材步骤进行。
