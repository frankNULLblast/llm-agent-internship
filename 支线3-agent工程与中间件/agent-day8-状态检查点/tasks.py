# 教材 Day 8 的最终完整 tasks.py（需合并进工程，替换 Day 3/4 探针与 Day 5 临时任务）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM 的 patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出，不伪造实跑日志。

import json
import os
from uuid import UUID

from celery import Celery
from celery.utils.log import get_task_logger
from kombu import Queue
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
from openai import APIConnectionError, APITimeoutError, RateLimitError
from psycopg import OperationalError as PsycopgOperationalError
from sqlalchemy import select
from sqlalchemy.exc import OperationalError as SqlalchemyOperationalError

from patent_bill import extract_with_usage
from storage import AgentRun, TERMINAL_STATUSES, add_event, session_scope
from workflow import build_graph


logger = get_task_logger(__name__)
celery_app = Celery(
    "patent_agent",
    broker=os.environ["CELERY_BROKER_URL"],
)
celery_app.conf.update(
    task_default_queue="agent.run",
    task_queues=(Queue("agent.run", durable=True),),
    task_default_delivery_mode=2,
    task_ignore_result=True,
    task_store_errors_even_if_ignored=False,
    task_publish_retry=False,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    broker_transport_options={"confirm_publish": True},
)

TRANSIENT_ERRORS = (
    TimeoutError,
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    PsycopgOperationalError,
    SqlalchemyOperationalError,
)


def write_log(event: str, **fields: object) -> None:
    logger.info(json.dumps({"event": event, **fields}, ensure_ascii=False))


def checkpoint_url() -> str:
    value = os.getenv("LANGGRAPH_DATABASE_URL")
    if not value:
        raise RuntimeError("未设置 LANGGRAPH_DATABASE_URL")
    return value


def configured_extractor():
    mode = os.getenv("AGENT_EXTRACTOR_MODE", "real")
    if mode == "real":
        return extract_with_usage
    if mode == "fake":
        from tests.fake_model import fake_extractor

        return fake_extractor
    raise RuntimeError("AGENT_EXTRACTOR_MODE 只能是 real 或 fake")


def graph_config(run_id: str) -> dict:
    return {"configurable": {"thread_id": run_id}}


def claim_task(run_id, task_id, request_id, attempt):
    with session_scope() as session:
        run = session.execute(
            select(AgentRun)
            .where(AgentRun.id == run_id)
            .with_for_update()
        ).scalar_one_or_none()
        if run is None:
            write_log("run_not_found", run_id=str(run_id), request_id=request_id, task_id=task_id)
            return None
        if (
            run.status in TERMINAL_STATUSES
            or run.status not in {"queued", "running"}
            or run.current_task_id != task_id
        ):
            add_event(
                session, run.id, "duplicate_or_stale_task_skipped",
                request_id, {"task_id": task_id, "status": run.status},
            )
            return None
        run.status = "running"
        add_event(
            session, run.id, "task_started",
            request_id, {"task_id": task_id, "attempt": attempt},
        )
        return dict(run.payload_json), dict(run.result_json or {})


def record_retry(run_id, task_id, request_id, attempt, exc) -> None:
    try:
        with session_scope() as session:
            run = session.execute(
                select(AgentRun).where(AgentRun.id == run_id).with_for_update()
            ).scalar_one_or_none()
            if (
                run is not None
                and run.status == "running"
                and run.current_task_id == task_id
            ):
                add_event(
                    session, run.id, "task_retry_scheduled",
                    request_id,
                    {"task_id": task_id, "attempt": attempt, "error_type": type(exc).__name__},
                )
    except Exception as log_error:
        write_log(
            "retry_event_write_failed", run_id=str(run_id),
            request_id=request_id, task_id=task_id,
            error_type=type(log_error).__name__,
        )


def save_waiting_review(run_id, task_id, request_id, review_snapshot, model_usage) -> None:
    with session_scope() as session:
        run = session.execute(
            select(AgentRun).where(AgentRun.id == run_id).with_for_update()
        ).scalar_one()
        if run.status == "waiting_review":
            add_event(session, run.id, "duplicate_waiting_write_skipped", request_id, {"task_id": task_id})
            return
        if run.status != "running" or run.current_task_id != task_id:
            add_event(session, run.id, "stale_waiting_write_skipped", request_id, {"task_id": task_id, "status": run.status})
            return
        run.status = "waiting_review"
        run.result_json = {"review_snapshot": review_snapshot}
        run.model_usage = model_usage
        add_event(session, run.id, "graph_waiting_review", request_id, {"task_id": task_id})


def save_terminal(run_id, task_id, request_id, final_result, model_usage) -> None:
    status = final_result.get("status")
    if status not in {"succeeded", "rejected"}:
        raise ValueError("图返回了非法终态")
    with session_scope() as session:
        run = session.execute(
            select(AgentRun).where(AgentRun.id == run_id).with_for_update()
        ).scalar_one()
        if run.status in TERMINAL_STATUSES:
            add_event(session, run.id, "duplicate_terminal_skipped", request_id, {"task_id": task_id, "status": run.status})
            return
        if run.status != "running" or run.current_task_id != task_id:
            add_event(session, run.id, "stale_terminal_skipped", request_id, {"task_id": task_id, "status": run.status})
            return
        run.status = status
        run.result_json = final_result
        if model_usage is not None:
            merged_usage = dict(run.model_usage or {})
            merged_usage.update(model_usage)
            run.model_usage = merged_usage
        run.error_code = None
        run.error_message = None
        add_event(session, run.id, "run_terminal", request_id, {"task_id": task_id, "status": status})


def save_failed(run_id, task_id, request_id, error_code) -> None:
    with session_scope() as session:
        run = session.execute(
            select(AgentRun).where(AgentRun.id == run_id).with_for_update()
        ).scalar_one_or_none()
        if run is None or run.status != "running" or run.current_task_id != task_id:
            return
        run.status = "failed"
        run.error_code = error_code
        run.error_message = "执行失败；请使用 request_id 查询脱敏事件"
        add_event(session, run.id, "run_failed", request_id, {"task_id": task_id, "error_code": error_code})


def retry_or_fail(task, run_id, task_id, request_id, attempt, exc):
    if task.request.retries >= task.max_retries:
        save_failed(run_id, task_id, request_id, "transient_retries_exhausted")
        return None
    record_retry(run_id, task_id, request_id, attempt, exc)
    raise task.retry(exc=exc, countdown=min(2 ** (task.request.retries + 1), 8))


@celery_app.task(bind=True, name="agent.execute", max_retries=2)
def execute_agent_run(self, run_id: str, request_id: str) -> None:
    run_uuid = UUID(run_id)
    task_id = self.request.id
    attempt = self.request.retries + 1
    try:
        claimed = claim_task(run_uuid, task_id, request_id, attempt)
        if claimed is None:
            return
        payload, _intermediate = claimed
        with PostgresSaver.from_conn_string(checkpoint_url()) as checkpointer:
            graph = build_graph(configured_extractor(), checkpointer)
            result = graph.invoke(
                {
                    "ocr_text": payload["ocr_text"],
                    "fee_records": payload["fee_records"],
                    "request_id": request_id,
                },
                graph_config(run_id),
                version="v2",
            )
        if not result.interrupts:
            raise RuntimeError("首次执行未到达人工复核")
        usage = dict(result.value.get("model_usage") or {})
        usage["task_attempt"] = attempt
        save_waiting_review(
            run_uuid, task_id, request_id, result.interrupts[0].value, usage
        )
        write_log("graph_waiting_review", run_id=run_id, request_id=request_id, task_id=task_id, attempt=attempt)
    except TRANSIENT_ERRORS as exc:
        retry_or_fail(self, run_uuid, task_id, request_id, attempt, exc)
    except Exception as exc:
        save_failed(run_uuid, task_id, request_id, "invalid_input_or_workflow_error")
        write_log("task_failed", run_id=run_id, request_id=request_id, task_id=task_id, attempt=attempt, error_type=type(exc).__name__)


@celery_app.task(bind=True, name="agent.resume", max_retries=2)
def resume_agent_run(self, run_id: str, request_id: str) -> None:
    run_uuid = UUID(run_id)
    task_id = self.request.id
    attempt = self.request.retries + 1
    try:
        claimed = claim_task(run_uuid, task_id, request_id, attempt)
        if claimed is None:
            return
        _payload, intermediate = claimed
        review = intermediate.get("human_review")
        if not isinstance(review, dict):
            raise ValueError("缺少已持久化的人工复核值")
        with PostgresSaver.from_conn_string(checkpoint_url()) as checkpointer:
            graph = build_graph(configured_extractor(), checkpointer)
            result = graph.invoke(
                Command(resume=review), graph_config(run_id), version="v2"
            )
        if result.interrupts:
            raise RuntimeError("恢复后仍停在未知人工节点")
        final_result = result.value.get("final_result")
        if not isinstance(final_result, dict):
            raise RuntimeError("恢复后没有终态")
        usage = dict(result.value.get("model_usage") or {})
        usage["resume_task_attempt"] = attempt
        save_terminal(run_uuid, task_id, request_id, final_result, usage)
        write_log("graph_terminal", run_id=run_id, request_id=request_id, task_id=task_id, attempt=attempt, status=final_result["status"])
    except TRANSIENT_ERRORS as exc:
        retry_or_fail(self, run_uuid, task_id, request_id, attempt, exc)
    except Exception as exc:
        save_failed(run_uuid, task_id, request_id, "resume_or_workflow_error")
        write_log("resume_failed", run_id=run_id, request_id=request_id, task_id=task_id, attempt=attempt, error_type=type(exc).__name__)


def publish_execute(run_id: str, request_id: str, task_id: str) -> None:
    execute_agent_run.apply_async(args=[run_id, request_id], task_id=task_id, queue="agent.run")


def publish_resume(run_id: str, request_id: str, task_id: str) -> None:
    resume_agent_run.apply_async(args=[run_id, request_id], task_id=task_id, queue="agent.run")
