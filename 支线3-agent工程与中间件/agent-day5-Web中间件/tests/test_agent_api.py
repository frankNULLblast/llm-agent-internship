# 教材 Day 5 离线契约测试（替换 PG/Redis/publisher 边界，不消费 RabbitMQ）。
# ⚠️ 可运行代码位置说明：当天真实跑通的代码在培训 VM 的 patent-agent-service。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出。

import json
import logging
from datetime import datetime
from uuid import UUID

from fastapi.testclient import TestClient
from kombu.exceptions import OperationalError as BrokerOperationalError

import main


client = TestClient(main.app)
RUN_ID = UUID("11111111-1111-1111-1111-111111111111")
VALID_PAYLOAD = {
    "ocr_text": "全部为虚构教学文本",
    "fee_records": [
        {
            "patent_application_number": "CN202410123456.7",
            "fee_type": "代理服务费",
            "amount_yuan": "3500.00",
        }
    ],
}


def run_view(status: str) -> dict:
    return {
        "run_id": RUN_ID,
        "status": status,
        "result": None,
        "model_usage": None,
        "error_code": None,
        "error_message": None,
        "created_at": datetime.fromisoformat("2026-07-31T00:00:00+00:00"),
        "updated_at": datetime.fromisoformat("2026-07-31T00:00:01+00:00"),
    }


def test_request_context_emits_correlated_log(caplog) -> None:
    caplog.set_level(logging.INFO, logger="uvicorn.error")
    response = client.get("/health", headers={"X-Request-ID": "offline-log-001"})
    assert response.status_code == 200
    messages = [record.getMessage() for record in caplog.records]
    assert any(
        '"event": "http_request"' in message
        and '"request_id": "offline-log-001"' in message
        for message in messages
    )


def test_create_returns_202_without_exposing_internal_fields(monkeypatch) -> None:
    published: list[str] = []
    monkeypatch.setattr(
        main,
        "create_or_get_run",
        lambda *_args: (run_view("enqueue_failed"), "created"),
    )

    def enqueue(_run_id, _task_id, _request_id, publish):
        publish()
        return run_view("queued")

    monkeypatch.setattr(main, "enqueue_created_run", enqueue)
    monkeypatch.setattr(
        main,
        "send_execute",
        lambda run_id, _request_id, _task_id: published.append(str(run_id)),
    )
    response = client.post(
        "/api/v1/agent-runs",
        headers={
            "Idempotency-Key": "offline-create",
            "X-Request-ID": "offline-request-001",
        },
        json=VALID_PAYLOAD,
    )
    assert response.status_code == 202
    assert response.json() == {"run_id": str(RUN_ID), "status": "queued"}
    assert response.headers["X-Request-ID"] == "offline-request-001"
    assert "X-Process-Time-Ms" in response.headers
    assert published == [str(RUN_ID)]


def test_same_request_returns_original_without_republish(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "create_or_get_run",
        lambda *_args: (run_view("running"), "same"),
    )
    monkeypatch.setattr(
        main,
        "enqueue_created_run",
        lambda *_args: (_ for _ in ()).throw(AssertionError("不得再次投递")),
    )
    response = client.post(
        "/api/v1/agent-runs",
        headers={"Idempotency-Key": "offline-same"},
        json=VALID_PAYLOAD,
    )
    assert response.status_code == 202
    assert response.json()["run_id"] == str(RUN_ID)


def test_same_key_different_body_is_409(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "create_or_get_run",
        lambda *_args: (run_view("queued"), "conflict"),
    )
    response = client.post(
        "/api/v1/agent-runs",
        headers={"Idempotency-Key": "offline-conflict"},
        json=VALID_PAYLOAD,
    )
    assert response.status_code == 409


def test_boundary_validation_is_422() -> None:
    missing_header = client.post("/api/v1/agent-runs", json=VALID_PAYLOAD)
    assert missing_header.status_code == 422

    wrong_amount_type = {
        **VALID_PAYLOAD,
        "fee_records": [
            {
                "patent_application_number": "CN202410123456.7",
                "fee_type": "代理服务费",
                "amount_yuan": 3500,
            }
        ],
    }
    response = client.post(
        "/api/v1/agent-runs",
        headers={"Idempotency-Key": "offline-bad-schema"},
        json=wrong_amount_type,
    )
    assert response.status_code == 422


def test_missing_run_is_404(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "read_terminal_cache",
        lambda _run_id: None,
        raising=False,
    )
    monkeypatch.setattr(main, "get_run", lambda _run_id: None)
    response = client.get("/api/v1/agent-runs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_broker_failure_is_503_and_records_enqueue_failure(monkeypatch) -> None:
    recorded: list[str] = []
    monkeypatch.setattr(
        main,
        "create_or_get_run",
        lambda *_args: (run_view("enqueue_failed"), "created"),
    )

    def broker_down(*_args):
        raise BrokerOperationalError("synthetic broker outage")

    monkeypatch.setattr(main, "enqueue_created_run", broker_down)
    monkeypatch.setattr(
        main,
        "mark_enqueue_failed",
        lambda run_id, _task_id, _request_id: recorded.append(str(run_id)),
    )
    response = client.post(
        "/api/v1/agent-runs",
        headers={"Idempotency-Key": "offline-broker-down"},
        json=VALID_PAYLOAD,
    )
    assert response.status_code == 503
    assert response.json()["detail"]["run_id"] == str(RUN_ID)
    assert recorded == [str(RUN_ID)]


def test_review_202_and_wrong_state_409(monkeypatch) -> None:
    published: list[str] = []

    def enqueue_review(_run_id, _review, _task_id, _request_id, publish):
        publish()
        return run_view("queued"), "queued"

    monkeypatch.setattr(main, "enqueue_review", enqueue_review)
    monkeypatch.setattr(
        main,
        "send_resume",
        lambda run_id, _request_id, _task_id: published.append(str(run_id)),
    )
    accepted = client.post(
        f"/api/v1/agent-runs/{RUN_ID}/review",
        json={"decision": "approve", "comment": "虚构样例"},
    )
    assert accepted.status_code == 202
    assert published == [str(RUN_ID)]

    monkeypatch.setattr(
        main,
        "enqueue_review",
        lambda *_args: (run_view("running"), "conflict"),
    )
    conflict = client.post(
        f"/api/v1/agent-runs/{RUN_ID}/review",
        json={"decision": "approve", "comment": "虚构样例"},
    )
    assert conflict.status_code == 409
