# 本文件对应教材 Day 4 的设计骨架（在 Day 3 的 celery 配置与 probe 之上新增 slow_probe_run）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM（Red Hat 8, 192.168.172.100）的
#   ~/llm-agent-internship/agent-middleware-plus/patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出，不伪造实跑日志。

import json
import os
import socket
import time
from uuid import UUID

from celery import Celery
from kombu import Queue
from sqlalchemy import select

from storage import AgentRun, TERMINAL_STATUSES, add_event, session_scope


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


@celery_app.task(name="agent.probe")
def probe(value: int) -> None:
    print(
        json.dumps(
            {
                "event": "probe_completed",
                "value": value,
                "doubled": value * 2,
                "worker": socket.gethostname(),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


@celery_app.task(bind=True, name="agent.slow_probe_run", max_retries=0)
def slow_probe_run(self, run_id: str, request_id: str) -> None:
    # 数据库探针任务：验证行锁 + 终态守卫下的幂等终态。
    # sleep 参数没有放进 Celery 消息，而是从 PostgreSQL 读取；任务消息仍只有 run_id/request_id。
    task_id = self.request.id

    with session_scope() as session:
        run = session.execute(
            select(AgentRun)
            .where(AgentRun.id == UUID(run_id))
            .with_for_update()
        ).scalar_one_or_none()
        if run is None:
            return
        if run.status in TERMINAL_STATUSES or run.current_task_id != task_id:
            add_event(
                session,
                run.id,
                "duplicate_or_stale_task_skipped",
                request_id,
                {"task_id": task_id},
            )
            return
        run.status = "running"
        seconds = int(run.payload_json["probe_seconds"])
        add_event(
            session,
            run.id,
            "probe_started",
            request_id,
            {"task_id": task_id, "seconds": seconds},
        )

    time.sleep(seconds)

    with session_scope() as session:
        run = session.execute(
            select(AgentRun)
            .where(AgentRun.id == UUID(run_id))
            .with_for_update()
        ).scalar_one()
        if run.status in TERMINAL_STATUSES:
            add_event(
                session,
                run.id,
                "duplicate_terminal_skipped",
                request_id,
                {"task_id": task_id},
            )
            return
        if run.current_task_id != task_id:
            add_event(
                session,
                run.id,
                "stale_terminal_skipped",
                request_id,
                {"task_id": task_id},
            )
            return
        run.status = "succeeded"
        run.result_json = {"kind": "day4_probe", "slept_seconds": seconds}
        add_event(
            session,
            run.id,
            "probe_succeeded",
            request_id,
            {"task_id": task_id},
        )
