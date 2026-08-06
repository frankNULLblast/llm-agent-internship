# 本文件对应教材 Day 3 的设计骨架（celery 配置 + probe 任务）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM（Red Hat 8, 192.168.172.100）的
#   ~/llm-agent-internship/agent-middleware-plus/patent-agent-service，提交号 e13000b。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出，不伪造实跑日志。
#   以下为教材 Day 3 原文代码（设计参考），用于说明队列设计与观察方法。

import json
import os
import socket

from celery import Celery
from kombu import Queue


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
    # 仅用于 Day 3 确认消息链路，不是业务结果。
    # task_ignore_result=True 是刻意设计：命令行返回的任务 ID 只是消息标识，
    # 不代表 PostgreSQL 中已有终态。
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
