# 教材 Day 9 的 ops/run_golden_cases.py（需合并进工程）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM 的 patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出。
# 脚本用真实 API/PG/Redis/RabbitMQ/两 Worker，但模型固定 fake。
# 不保存 OCR，只把 case 名、run ID、终态、route、脱敏错误码、usage 写进报告。

import json
import os
import time
from copy import deepcopy
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select

from storage import AgentRun, AgentRunEvent, session_scope
from tasks import resume_agent_run


BASE_URL = os.getenv("AGENT_BASE_URL", "http://127.0.0.1:8000")
VALID_FEES = [
    {
        "patent_application_number": "CN202410123456.7",
        "fee_type": "代理服务费",
        "amount_yuan": "3500.00",
    }
]
BASE_OCR = (
    "虚构电子发票：申请号 CN202410123456.7，"
    "发票号 24503100000123456789，日期 2026-07-10，"
    "购买方示例智能科技有限公司，"
    "销售方示例知识产权服务有限公司，"
    "项目发明专利申请代理服务费，金额 3500.00 元。"
)

client = httpx.Client(base_url=BASE_URL, timeout=5.0)
report: list[dict] = []


def read_run(run_id: str) -> dict:
    response = client.get(f"/api/v1/agent-runs/{run_id}")
    response.raise_for_status()
    return response.json()


def wait_for(run_id: str, expected: set[str], seconds: int = 30) -> dict:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        run = read_run(run_id)
        if run["status"] in expected:
            return run
        time.sleep(0.25)
    raise AssertionError(f"run {run_id} 未在 {seconds}s 内进入 {sorted(expected)}")


def create_case(name: str, ocr_text: str, fee_records: list[dict]) -> str:
    key = f"golden-{name}-{uuid4()}"
    request_id = f"gc-{uuid4()}"
    payload = {"ocr_text": ocr_text, "fee_records": fee_records}
    first = client.post(
        "/api/v1/agent-runs",
        headers={"Idempotency-Key": key, "X-Request-ID": request_id},
        json=payload,
    )
    assert first.status_code == 202, first.text
    run_id = first.json()["run_id"]

    same = client.post(
        "/api/v1/agent-runs",
        headers={"Idempotency-Key": key, "X-Request-ID": f"{request_id}-same"},
        json=payload,
    )
    assert same.status_code == 202, same.text
    assert same.json()["run_id"] == run_id
    return run_id


def run_review_case(name, marker, decision, expected_status, expected_route) -> str:
    run_id = create_case(name, f"{marker}\n{BASE_OCR}", VALID_FEES)
    waiting = wait_for(run_id, {"waiting_review", "failed"})
    assert waiting["status"] == "waiting_review", waiting

    response = client.post(
        f"/api/v1/agent-runs/{run_id}/review",
        headers={"X-Request-ID": f"gr-{uuid4()}"},  # noqa: E501
        json={"decision": decision, "comment": f"虚构 golden case：{name}"},
    )
    assert response.status_code == 202, response.text
    final = wait_for(run_id, {expected_status, "failed"})
    assert final["status"] == expected_status, final
    assert final["result"]["bill_review"]["route"] == expected_route
    report.append(
        {
            "case": name,
            "run_id": run_id,
            "status": final["status"],
            "route": final["result"]["bill_review"]["route"],
            "model_usage": final["model_usage"],
        }
    )
    return run_id


def run_failure_case(name, marker, fee_records) -> str:
    run_id = create_case(name, f"{marker}\n{BASE_OCR}", fee_records)
    final = wait_for(run_id, {"failed", "waiting_review"})
    assert final["status"] == "failed", final
    assert final["error_code"] is not None
    report.append(
        {
            "case": name,
            "run_id": run_id,
            "status": final["status"],
            "error_code": final["error_code"],
        }
    )
    return run_id


def prove_duplicate_terminal_is_ignored(run_id: str) -> None:
    run_uuid = UUID(run_id)
    with session_scope() as session:
        run = session.get(AgentRun, run_uuid)
        assert run is not None
        task_id = run.current_task_id
        before = deepcopy(run.result_json)
        assert task_id is not None

    # 用终态 run 的原 task ID 再次发布，断言产生 skip 事件且终态不变。
    resume_agent_run.apply_async(
        args=[run_id, "golden-duplicate-redelivery"],
        task_id=task_id,
        queue="agent.run",
    )

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        with session_scope() as session:
            event = session.scalar(
                select(AgentRunEvent)
                .where(AgentRunEvent.run_id == run_uuid)
                .where(AgentRunEvent.event_type == "duplicate_or_stale_task_skipped")
                .order_by(AgentRunEvent.id.desc())
            )
            run = session.get(AgentRun, run_uuid)
            if event is not None:
                assert run is not None
                assert run.result_json == before
                assert run.status == "succeeded"
                return
        time.sleep(0.25)
    raise AssertionError("重复消息没有产生 skip 事件")


def main() -> int:
    run_review_case("standard_approve", "", "approve", "succeeded", "standard_manual_review")
    run_review_case("priority_approve", "[PRIORITY_REVIEW]", "approve", "succeeded", "priority_manual_review")
    run_review_case("human_reject", "", "reject", "rejected", "standard_manual_review")
    run_failure_case("structured_output_error", "[BAD_MODEL_OUTPUT]", VALID_FEES)
    run_failure_case(
        "fee_business_error", "",
        [{"patent_application_number": "CN202410123456.7", "fee_type": "代理服务费", "amount_yuan": "0.00"}],
    )
    duplicate_run_id = run_review_case("duplicate_delivery", "", "approve", "succeeded", "standard_manual_review")
    prove_duplicate_terminal_is_ignored(duplicate_run_id)
    report[-1]["duplicate_terminal_ignored"] = True

    output = Path(os.getenv("GOLDEN_OUTPUT", "evidence/day9/golden-results.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"golden cases: 6 passed; report={output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        client.close()
