# 教材 Day 7 的 test_workflow.py（需合并进工程）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM 的 patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出。

from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from workflow import build_graph


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
VALID_FEES = [
    {
        "patent_application_number": "CN202410123456.7",
        "fee_type": "代理服务费",
        "amount_yuan": "3500.00",
    }
]


def fake_extractor(_text: str) -> tuple[dict, dict]:
    return dict(VALID_RECORD), {
        "model": "fake-extractor-v1",
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30,
        "latency_ms": 1.0,
    }


def initial_input(fee_records: list[dict] | None = None) -> dict:
    return {
        "ocr_text": "全部为虚构教学文本",
        "fee_records": VALID_FEES if fee_records is None else fee_records,
        "request_id": str(uuid4()),
    }


def new_run():
    graph = build_graph(fake_extractor, InMemorySaver())
    config = {"configurable": {"thread_id": str(uuid4())}}
    first = graph.invoke(initial_input(), config, version="v2")
    assert first.interrupts
    assert first.value.get("final_result") is None
    return graph, config, first


def test_approve_resumes_same_thread() -> None:
    graph, config, first = new_run()
    assert first.interrupts[0].value["kind"] == "patent_bill_human_review"
    final = graph.invoke(
        Command(resume={"decision": "approve", "comment": "虚构样例已人工复核"}),
        config,
        version="v2",
    )
    assert not final.interrupts
    assert final.value["final_result"]["status"] == "succeeded"
    assert final.value["fee_summary"]["total_yuan"] == "3500.00"


def test_reject_resumes_same_thread() -> None:
    graph, config, _first = new_run()
    final = graph.invoke(
        Command(resume={"decision": "reject", "comment": "虚构样例字段需重新提供"}),
        config,
        version="v2",
    )
    assert final.value["final_result"]["status"] == "rejected"
    assert final.value["final_result"]["decision"] == "reject"


def test_bad_model_output_fails_before_interrupt() -> None:
    def bad_extractor(_text: str) -> tuple[dict, dict]:
        return {"document_type": "电子发票"}, {}

    graph = build_graph(bad_extractor, InMemorySaver())
    config = {"configurable": {"thread_id": str(uuid4())}}
    with pytest.raises(ValueError):
        graph.invoke(initial_input(), config, version="v2")


def test_bad_fee_input_fails_before_interrupt() -> None:
    graph = build_graph(fake_extractor, InMemorySaver())
    config = {"configurable": {"thread_id": str(uuid4())}}
    bad_fees = [
        {
            "patent_application_number": "CN202410123456.7",
            "fee_type": "代理服务费",
            "amount_yuan": "0.00",
        }
    ]
    with pytest.raises(ValueError):
        graph.invoke(initial_input(bad_fees), config, version="v2")


def test_invalid_resume_value_is_rejected() -> None:
    graph, config, _first = new_run()
    with pytest.raises(ValueError):
        graph.invoke(
            Command(resume={"decision": "skip", "comment": ""}),
            config,
            version="v2",
        )


def test_too_long_comment_is_rejected() -> None:
    graph, config, _first = new_run()
    with pytest.raises(ValueError):
        graph.invoke(
            Command(resume={"decision": "approve", "comment": "x" * 501}),
            config,
            version="v2",
        )
