# Day 5 每日总结

日期：2026-07-17（星期五）

## 今日完成
- 完成 Day 5「专利票据识别 Demo 与第一周考核」。
- 交付从脱敏 OCR 文本抽取专利/票据字段、做确定性检查、进入人工复核队列的 Python CLI。
- 三个文件放仓库 `week1/day05/`：
  - `patent_bill_ocr.txt`：虚构教学样例 OCR 文本（明确标注非真实票据）。
  - `patent_bill.py`：`validate` / `review_reasons` / `build_result` / `extract` / `main`，抽 9 个固定字段、做类型与业务样例校验、分流人工复核。
  - `test_patent_bill.py`：5 个离线 `unittest`，**不调 API、不产生费用**。
- 挑战任务（图片/PDF OCR 输入）保持 `extract(text: str)` 接口不变，本期仅完成固定文本基线，OCR 接入留作后续扩展（见下方「挑战任务处理」）。

## 验证结果（诚实记录）
- ✅ 离线测试：`python -m unittest -v` → 5 个用例全部 **OK**（标准复核 / 低置信度 / 错申请号 / 缺金额 / 额外字段被拒）。
- ✅ 在线真实调用（模型 `deepseek-chat`，覆盖环境预设的 `deepseek-v1-tflash`）：
  - `python patent_bill.py patent_bill_ocr.txt -o result.json` → 退出码 **0**，写入 `result.json`。
  - `result.json` 的 `record` 含 9 个固定字段，申请号 `CN202410123456.7`、金额 `3500.0`、置信度 `0.95`，`route=standard_manual_review`、`review_reasons=[]`。

## 人工核对记录（逐字段对照原文）
| 字段 | OCR 原文 | 抽取 record | 一致 |
|---|---|---|---|
| document_type | 票据类型：电子发票 | 电子发票 | ✅ |
| patent_application_number | CN202410123456.7 | CN202410123456.7 | ✅ |
| invoice_number | 24503100000123456789 | 24503100000123456789 | ✅ |
| issue_date | 2026-07-10 | 2026-07-10 | ✅ |
| payer | 示例智能科技有限公司 | 示例智能科技有限公司 | ✅ |
| payee | 示例知识产权服务有限公司 | 示例知识产权服务有限公司 | ✅ |
| service_item | 发明专利申请代理服务费 | 发明专利申请代理服务费 | ✅ |
| amount_yuan | 价税合计 3500.00 元 | 3500.0 | ✅ |
| confidence | （模型自评，原文无） | 0.95 | — 复核信号 |

> 结论：9 个原文字段全部正确抽取，无幻觉、无补字段；程序分流进入标准人工复核队列。**两种 route 都只表示「等待人工复核」，本 Demo 不判断票据真伪、合规或已批准。**

## 三个我现在能讲清楚的概念
1. **模型与程序的责任边界**：模型擅长处理版式/措辞变化（从自由文本抽字段）；程序擅长确定性的字段、类型、业务样例检查。模型输出不能盲信，必须再过一遍 `validate`。
2. **confidence 只是复核信号**：模型给的 `confidence` 不是校准过的真实概率，低于 0.85 只代表「建议优先人工看一眼」，绝不是错误或拒绝。
3. **未知字段用 null，不猜测**：prompt 里要求未知值写 `null`，再由人工逐字段核对，避免模型补出原文没有的内容。

## 卡住的点与处理
- **环境预设 `DEEPSEEK_MODEL=deepseek-v1-tflash` 官方 endpoint 拒收（400）**：沿用 Day 4 的经验，运行前 `DEEPSEEK_MODEL=deepseek-chat` 覆盖，在线调用跑通。
- **`extra_body={"thinking": {"type": "disabled"}}` 是否被 `deepseek-chat` 接受**：实测接受、未报错（该参数本用于推理模型，对非推理模型被安全忽略）。保持教程原样。
- **挑战任务（图片/PDF OCR 输入）未接**：教程明确「只有图片输入成为明确要求时再接 OCR」。本期保持 `extract(text: str)` 接口与固定文本测试不变，OCR 接入作为后续扩展，不阻塞验收。

## 每日总结要记的两笔（验收清单对照）
- 离线 5 测试全 OK；关键字段缺失进入优先复核，额外字段不能绕过 Schema。
- 一次在线真实调用产出 `result.json`（UTF-8、可被 `json.tool` 解析），两种 route 都保留人工复核。

## 明日计划
- Day 5 验收清单 6 条达成；下一步进入 Day 6：软件开发全过程与专利费用计算器（需求/设计/编码/集成/测试/上线六阶段），这是 FastAPI 加餐的前置。

## 阶段小测（自答）
1. OCR 把图片/PDF 转文本；大模型从文本抽语义字段。
2. 模型输出必须再过 Python 的字段、类型、业务样例规则检查。
3. 置信度是复核信号，不是真实概率或批准依据。
4. API Key 与真实票据不得写入仓库或测试材料。
5. 未知字段应返回 `null`，不能猜测。

## 挑战任务处理
- 要求：接入一种图片/PDF OCR 输入，但保持 `extract(text: str)` 接口和固定文本测试不变。
- 本期状态：完成固定文本基线（`patent_bill_ocr.txt` + 离线测试覆盖）。OCR 接入（如调用 OCR 服务或本地库，先 `ocr_to_text(path) -> str` 再传 `extract`）留待图片输入成为明确要求时再做，不破坏现有接口与测试。
