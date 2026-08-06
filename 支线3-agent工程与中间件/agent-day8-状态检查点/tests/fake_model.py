# 教材 Day 8 的固定 fake extractor，含 Day 9 扩展的故障开关。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM 的 patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出。
# 输出固定、无网络、无随机数。AGENT_EXTRACTOR_MODE 未设置时 Worker 用真实模型；
# 测试 Worker 显式设为 fake。

import time

import httpx
from openai import RateLimitError

VALID_RECORD = {
    "document_type": "电子发票",
    "patent_application_number": "CN202410123456.7",
    "invoice_number": "24503100000123456789",
    "issue_date": "2026-07-10",
    "payer": "示例智能科技有限公司",
    "payee": "示例知识产权服务有限公司",
    "service_item": "发明专利申请代理服务费",
    "amount_yuan": 3500.0,
    "confidence": 0.95,
}


def fake_extractor(text: str) -> tuple[dict, dict]:
    # Day 9 故障开关（在 fake_extractor 最前面）。
    if "[MODEL_DELAY_15]" in text:
        time.sleep(15)
    if "[MODEL_429]" in text:
        raise RateLimitError(
            "synthetic rate limit",
            response=httpx.Response(
                429,
                request=httpx.Request("POST", "https://api.invalid"),
            ),
            body={"error": {"message": "synthetic rate limit"}},
        )
    # Day 8 故障开关。
    if "[MODEL_TIMEOUT]" in text:
        raise TimeoutError("synthetic timeout")
    if "[BAD_MODEL_OUTPUT]" in text:
        return {"document_type": "电子发票"}, {
            "model": "fake-extractor-v1",
            "prompt_tokens": 8,
            "completion_tokens": 2,
            "total_tokens": 10,
            "latency_ms": 1.0,
        }

    record = dict(VALID_RECORD)
    if "[PRIORITY_REVIEW]" in text:
        record["confidence"] = 0.60
    return record, {
        "model": "fake-extractor-v1",
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30,
        "latency_ms": 1.0,
    }
