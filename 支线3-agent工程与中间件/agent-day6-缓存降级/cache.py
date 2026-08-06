# 教材 Day 6 的 cache.py（需合并进工程）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM 的 patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出。

import json
import logging
import os
from functools import lru_cache
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError

from storage import TERMINAL_STATUSES


CACHE_TTL_SECONDS = 300
REQUIRED_CACHE_FIELDS = frozenset(
    {
        "run_id",
        "status",
        "result",
        "model_usage",
        "error_code",
        "error_message",
        "created_at",
        "updated_at",
    }
)
logger = logging.getLogger("patent_agent.cache")


def cache_key(run_id: UUID) -> str:
    return f"agent:run:{run_id}"


@lru_cache(maxsize=1)
def redis_client() -> Redis:
    value = os.getenv("REDIS_URL")
    if not value:
        raise RuntimeError("未设置 REDIS_URL")
    return Redis.from_url(
        value,
        decode_responses=True,
        socket_connect_timeout=0.5,
        socket_timeout=0.5,
        health_check_interval=30,
    )


def read_terminal_cache(run_id: UUID) -> str | None:
    try:
        raw = redis_client().get(cache_key(run_id))
        if raw is None:
            return None
        value = json.loads(raw)
        if (
            not isinstance(value, dict)
            or set(value) != REQUIRED_CACHE_FIELDS
            or value.get("run_id") != str(run_id)
            or value.get("status") not in TERMINAL_STATUSES
        ):
            redis_client().delete(cache_key(run_id))
            return None
        return raw
    except (RedisError, ValueError, TypeError):
        logger.warning(
            json.dumps({"event": "cache_get_failed", "run_id": str(run_id)})
        )
        return None


def write_terminal_cache(run: dict) -> bool:
    if run.get("status") not in TERMINAL_STATUSES:
        return False
    run_id = UUID(str(run["run_id"]))
    payload = {
        **run,
        "run_id": str(run_id),
        "created_at": run["created_at"].isoformat(),
        "updated_at": run["updated_at"].isoformat(),
    }
    try:
        redis_client().setex(
            cache_key(run_id),
            CACHE_TTL_SECONDS,
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        )
        return True
    except (RedisError, ValueError, TypeError):
        logger.warning(
            json.dumps({"event": "cache_set_failed", "run_id": str(run_id)})
        )
        return False


def delete_terminal_cache(run_id: UUID) -> None:
    try:
        redis_client().delete(cache_key(run_id))
    except RedisError:
        logger.warning(
            json.dumps({"event": "cache_delete_failed", "run_id": str(run_id)})
        )
