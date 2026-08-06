# 教材 Day 5 对 storage.py 的扩展片段（需合并进 storage.py）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM 的 patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出。

from typing import Callable, Literal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from storage import AgentRun, add_event, run_to_dict, session_scope
from uuid import UUID


CreateOutcome = Literal["created", "same", "conflict"]


def create_or_get_run(
    idempotency_key: str,
    request_hash: str,
    payload: dict,
    request_id: str,
) -> tuple[dict, CreateOutcome]:
    # 数据库唯一约束仍是并发裁决者；Python 先查后插只优化常见路径。
    try:
        with session_scope() as session:
            existing = session.scalar(
                select(AgentRun).where(
                    AgentRun.idempotency_key == idempotency_key
                )
            )
            if existing is not None:
                outcome: CreateOutcome = (
                    "same"
                    if existing.request_hash == request_hash
                    else "conflict"
                )
                return run_to_dict(existing), outcome

            run = AgentRun(
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                status="enqueue_failed",
                payload_json=payload,
            )
            session.add(run)
            session.flush()
            add_event(session, run.id, "run_created", request_id)
            return run_to_dict(run), "created"
    except IntegrityError:
        # 两个同 key 请求并发插入时，数据库唯一约束裁决。
        with session_scope() as session:
            existing = session.scalar(
                select(AgentRun).where(
                    AgentRun.idempotency_key == idempotency_key
                )
            )
            if existing is None:
                raise
            outcome = (
                "same"
                if existing.request_hash == request_hash
                else "conflict"
            )
            return run_to_dict(existing), outcome


def get_run(run_id: UUID) -> dict | None:
    with session_scope() as session:
        run = session.get(AgentRun, run_id)
        return None if run is None else run_to_dict(run)


def enqueue_created_run(
    run_id: UUID,
    task_id: str,
    request_id: str,
    publish: Callable[[], None],
) -> dict:
    # 短行锁事务内完成一次 publisher-confirm 发布，再提交 queued。
    with session_scope() as session:
        run = session.execute(
            select(AgentRun)
            .where(AgentRun.id == run_id)
            .with_for_update()
        ).scalar_one()
        if run.status != "enqueue_failed":
            return run_to_dict(run)
        run.current_task_id = task_id
        publish()
        run.status = "queued"
        run.error_code = None
        run.error_message = None
        add_event(
            session,
            run.id,
            "run_queued",
            request_id,
            {"task_id": task_id},
        )
        session.flush()
        return run_to_dict(run)


def mark_enqueue_failed(
    run_id: UUID,
    task_id: str,
    request_id: str,
) -> None:
    with session_scope() as session:
        run = session.execute(
            select(AgentRun)
            .where(AgentRun.id == run_id)
            .with_for_update()
        ).scalar_one()
        if run.status == "enqueue_failed":
            run.error_code = "broker_unavailable"
            run.error_message = "任务暂未投递，请使用相同幂等键重试"
            add_event(
                session,
                run.id,
                "enqueue_failed",
                request_id,
                {"task_id": task_id},
            )


def enqueue_review(
    run_id: UUID,
    review: dict,
    task_id: str,
    request_id: str,
    publish: Callable[[], None],
) -> tuple[dict | None, Literal["queued", "not_found", "conflict"]]:
    with session_scope() as session:
        run = session.execute(
            select(AgentRun)
            .where(AgentRun.id == run_id)
            .with_for_update()
        ).scalar_one_or_none()
        if run is None:
            return None, "not_found"
        if run.status != "waiting_review":
            return run_to_dict(run), "conflict"

        intermediate = dict(run.result_json or {})
        intermediate["human_review"] = review
        run.result_json = intermediate
        run.current_task_id = task_id
        publish()
        run.status = "queued"
        add_event(
            session,
            run.id,
            "review_submitted",
            request_id,
            {
                "task_id": task_id,
                "decision": review["decision"],
                "comment_length": len(review["comment"]),
            },
        )
        session.flush()
        return run_to_dict(run), "queued"


def record_resume_enqueue_failed(
    run_id: UUID,
    task_id: str,
    request_id: str,
) -> None:
    with session_scope() as session:
        run = session.execute(
            select(AgentRun)
            .where(AgentRun.id == run_id)
            .with_for_update()
        ).scalar_one()
        if run.status == "waiting_review":
            add_event(
                session,
                run.id,
                "resume_enqueue_failed",
                request_id,
                {"task_id": task_id},
            )
