# 教材 Day 5 临时任务（需合并进 tasks.py）。
# ⚠️ 这些任务只用于证明 API 没有直接执行 Agent，当天验收后清理消息；
#    Day 8 会用真实 LangGraph 执行体完整替换。本仓库仅保留设计。


@celery_app.task(name="agent.execute")
def execute_agent_run(run_id: str, request_id: str) -> None:
    print(
        json.dumps(
            {
                "event": "day5_execute_received",
                "run_id": run_id,
                "request_id": request_id,
            }
        ),
        flush=True,
    )


@celery_app.task(name="agent.resume")
def resume_agent_run(run_id: str, request_id: str) -> None:
    print(
        json.dumps(
            {
                "event": "day5_resume_received",
                "run_id": run_id,
                "request_id": request_id,
            }
        ),
        flush=True,
    )


def publish_execute(run_id: str, request_id: str, task_id: str) -> None:
    execute_agent_run.apply_async(
        args=[run_id, request_id],
        task_id=task_id,
        queue="agent.run",
    )


def publish_resume(run_id: str, request_id: str, task_id: str) -> None:
    resume_agent_run.apply_async(
        args=[run_id, request_id],
        task_id=task_id,
        queue="agent.run",
    )
