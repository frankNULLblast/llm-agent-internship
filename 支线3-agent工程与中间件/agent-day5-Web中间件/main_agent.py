# 教材 Day 5 对 main.py 的扩展片段（需合并进 main.py）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM 的 patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出。
# 本片段依赖既有的 app / StrictModel / FeeRecord / Field / HTTPException 等定义。

import hashlib
import json
import logging
import os
import re
from datetime import datetime
from time import perf_counter
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Header, Request
from fastapi.responses import JSONResponse
from kombu import Connection
from kombu.exceptions import OperationalError as BrokerOperationalError
from pydantic import Field, field_validator
from redis import Redis
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from storage import (
    create_or_get_run,
    enqueue_created_run,
    enqueue_review,
    get_engine,
    get_run,
    mark_enqueue_failed,
    record_resume_enqueue_failed,
)


RunStatus = Literal[
    "enqueue_failed",
    "queued",
    "running",
    "waiting_review",
    "succeeded",
    "rejected",
    "failed",
]


class AgentRunCreate(StrictModel):
    ocr_text: str = Field(min_length=1, max_length=8000)
    fee_records: list[FeeRecord] = Field(min_length=1, max_length=100)

    @field_validator("ocr_text")
    @classmethod
    def ocr_text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("ocr_text 不能只包含空白")
        return value


class AgentReviewCreate(StrictModel):
    decision: Literal["approve", "reject"]
    comment: str = Field(max_length=500)


class AgentRunAccepted(StrictModel):
    run_id: UUID
    status: RunStatus


class AgentRunView(StrictModel):
    run_id: UUID
    status: RunStatus
    result: dict | None
    model_usage: dict | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


def accepted_view(run: dict) -> AgentRunAccepted:
    return AgentRunAccepted(run_id=run["run_id"], status=run["status"])


# ---- 安全日志中间件 ----
logger = logging.getLogger("uvicorn.error")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def safe_request_id(value: str | None) -> str:
    if value and REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return str(uuid4())


def write_log(event: str, **fields: object) -> None:
    logger.info(json.dumps({"event": event, **fields}, ensure_ascii=False))


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = safe_request_id(request.headers.get("X-Request-ID"))
    request.state.request_id = request_id
    started = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        write_log(
            "http_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=500,
            elapsed_ms=round((perf_counter() - started) * 1000, 2),
        )
        raise
    elapsed_ms = round((perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    write_log(
        "http_request",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        elapsed_ms=elapsed_ms,
    )
    return response


# ---- 哈希、投递与数据库故障处理 ----
def canonical_hash(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def request_id_of(request: Request) -> str:
    return request.state.request_id


def send_execute(run_id: UUID, request_id: str, task_id: str) -> None:
    # 延迟导入，旧接口的离线测试不会因 broker 配置而导入 Celery。
    from tasks import publish_execute

    publish_execute(str(run_id), request_id, task_id)


def send_resume(run_id: UUID, request_id: str, task_id: str) -> None:
    from tasks import publish_resume

    publish_resume(str(run_id), request_id, task_id)


@app.exception_handler(OperationalError)
async def database_unavailable(request: Request, exc: OperationalError) -> JSONResponse:
    write_log(
        "postgres_unavailable",
        request_id=request_id_of(request),
        error_type=type(exc).__name__,
    )
    return JSONResponse(status_code=503, content={"detail": "PostgreSQL 暂时不可用"})


# ---- 创建与查询接口 ----
@app.post(
    "/api/v1/agent-runs",
    response_model=AgentRunAccepted,
    status_code=202,
    tags=["agent runs"],
)
def create_agent_run(
    payload: AgentRunCreate,
    request: Request,
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=1, max_length=128),
    ],
) -> AgentRunAccepted:
    if not IDEMPOTENCY_PATTERN.fullmatch(idempotency_key):
        raise HTTPException(
            status_code=422,
            detail="Idempotency-Key 只能包含字母、数字、点、下划线、冒号和短横线",
        )

    request_id = request_id_of(request)
    body = payload.model_dump()
    run, outcome = create_or_get_run(
        idempotency_key,
        canonical_hash(body),
        body,
        request_id,
    )
    if outcome == "conflict":
        raise HTTPException(
            status_code=409,
            detail="同一 Idempotency-Key 已用于不同请求",
        )

    run_id = UUID(str(run["run_id"]))
    if run["status"] != "enqueue_failed":
        return accepted_view(run)

    task_id = str(uuid4())
    try:
        queued = enqueue_created_run(
            run_id,
            task_id,
            request_id,
            lambda: send_execute(run_id, request_id, task_id),
        )
    except BrokerOperationalError as exc:
        mark_enqueue_failed(run_id, task_id, request_id)
        write_log(
            "enqueue_failed",
            request_id=request_id,
            run_id=str(run_id),
            task_id=task_id,
            error_type=type(exc).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail={
                "code": "broker_unavailable",
                "run_id": str(run_id),
                "message": "请在 RabbitMQ 恢复后用相同请求和幂等键重试",
            },
        ) from exc
    return accepted_view(queued)


@app.get(
    "/api/v1/agent-runs/{run_id}",
    response_model=AgentRunView,
    tags=["agent runs"],
)
def read_agent_run(run_id: UUID) -> AgentRunView:
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run 不存在")
    return AgentRunView.model_validate(run)


# ---- 人工复核接口 ----
@app.post(
    "/api/v1/agent-runs/{run_id}/review",
    response_model=AgentRunAccepted,
    status_code=202,
    tags=["agent runs"],
)
def review_agent_run(
    run_id: UUID,
    review: AgentReviewCreate,
    request: Request,
) -> AgentRunAccepted:
    request_id = request_id_of(request)
    task_id = str(uuid4())
    try:
        run, outcome = enqueue_review(
            run_id,
            review.model_dump(),
            task_id,
            request_id,
            lambda: send_resume(run_id, request_id, task_id),
        )
    except BrokerOperationalError as exc:
        record_resume_enqueue_failed(run_id, task_id, request_id)
        write_log(
            "resume_enqueue_failed",
            request_id=request_id,
            run_id=str(run_id),
            task_id=task_id,
            error_type=type(exc).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail="RabbitMQ 暂时不可用，复核决定未入队，请重试",
        ) from exc
    if outcome == "not_found":
        raise HTTPException(status_code=404, detail="run 不存在")
    if outcome == "conflict":
        raise HTTPException(
            status_code=409,
            detail="只有 waiting_review 状态可以提交复核",
        )
    assert run is not None
    return accepted_view(run)


# ---- /ready ----
@app.get("/ready", tags=["system"])
def ready() -> JSONResponse:
    checks = {
        "postgresql": "ok",
        "rabbitmq": "ok",
        "redis": "ok",
    }
    ready_for_traffic = True

    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        checks["postgresql"] = "unavailable"
        ready_for_traffic = False

    try:
        with Connection(
            os.environ["CELERY_BROKER_URL"], connect_timeout=2
        ) as connection:
            connection.ensure_connection(max_retries=0)
    except Exception:
        checks["rabbitmq"] = "unavailable"
        ready_for_traffic = False

    try:
        redis_check = Redis.from_url(
            os.environ["REDIS_URL"],
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        try:
            redis_check.ping()
        finally:
            redis_check.close()
    except Exception:
        checks["redis"] = "degraded"

    return JSONResponse(
        status_code=200 if ready_for_traffic else 503,
        content={
            "status": "ready" if ready_for_traffic else "not_ready",
            "checks": checks,
        },
    )
