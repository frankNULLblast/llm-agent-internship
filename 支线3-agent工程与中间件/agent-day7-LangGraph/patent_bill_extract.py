# 教材 Day 7 对 patent_bill.py 的扩展片段（diff 形式；需合并进 patent_bill.py）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM 的 patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出。
# 下方以「最终文件内容」呈现四个变更点（保留原 extract() 契约）。

from time import perf_counter

# 原 import 保持不变；仅新增 perf_counter。


def extract_with_usage(text: str) -> tuple[dict, dict]:
    # 返回 (record, usage)；SDK 自动重试设为 0，Day 8 由 Celery 统一做有限重试。
    if not text or len(text) > 8000:
        raise ValueError("OCR 文本为空或超过 8000 字符")
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("未设置 DEEPSEEK_API_KEY")
    client = OpenAI(
        api_key=key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        timeout=30.0,
        max_retries=0,
    )
    # example = { 原字段示例保持不变 }
    started = perf_counter()
    response = client.chat.completions.create(
        # 原 model、messages、response_format、max_tokens 保持不变
    )
    latency_ms = round((perf_counter() - started) * 1000, 2)
    content = response.choices[0].message.content
    if not content:
        raise ValueError("模型返回空内容，请重试")
    usage = response.usage
    return validate(json.loads(content)), {
        "model": response.model,
        "prompt_tokens": 0 if usage is None else usage.prompt_tokens,
        "completion_tokens": 0 if usage is None else usage.completion_tokens,
        "total_tokens": 0 if usage is None else usage.total_tokens,
        "latency_ms": latency_ms,
    }


def extract(text: str) -> dict:
    # 旧 CLI 与旧测试继续调用 extract()，返回值仍是 dict。
    record, _usage = extract_with_usage(text)
    return record
