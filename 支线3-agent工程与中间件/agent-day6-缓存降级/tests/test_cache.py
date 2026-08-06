# 教材 Day 6 缓存测试片段（需合并进 tests/test_integration.py 与 test_agent_api.py）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM 的 patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出。

import json
from datetime import datetime
from uuid import uuid4

from cache import (
    CACHE_TTL_SECONDS,
    cache_key,
    read_terminal_cache,
    redis_client,
    write_terminal_cache,
)
import main


def test_only_terminal_run_is_cached() -> None:
    run_id = uuid4()
    terminal = {
        "run_id": run_id,
        "status": "succeeded",
        "result": {"decision": "approve"},
        "model_usage": None,
        "error_code": None,
        "error_message": None,
        "created_at": datetime.fromisoformat("2026-07-31T00:00:00+00:00"),
        "updated_at": datetime.fromisoformat("2026-07-31T00:00:01+00:00"),
    }
    assert write_terminal_cache(terminal) is True
    cached = read_terminal_cache(run_id)
    assert cached is not None
    assert json.loads(cached)["run_id"] == str(run_id)
    redis_client().delete(cache_key(run_id))

    non_terminal = {**terminal, "status": "waiting_review"}
    assert write_terminal_cache(non_terminal) is False
    assert read_terminal_cache(run_id) is None


def test_terminal_cache_ttl_is_bounded() -> None:
    run_id = uuid4()
    terminal = {
        "run_id": run_id,
        "status": "failed",
        "result": None,
        "model_usage": None,
        "error_code": "fake_failure",
        "error_message": "虚构的脱敏错误",
        "created_at": datetime.fromisoformat("2026-07-31T00:00:00+00:00"),
        "updated_at": datetime.fromisoformat("2026-07-31T00:00:01+00:00"),
    }
    assert write_terminal_cache(terminal) is True
    ttl = redis_client().ttl(cache_key(run_id))
    assert 0 < ttl <= CACHE_TTL_SECONDS
    redis_client().delete(cache_key(run_id))


def test_malformed_cache_value_is_discarded() -> None:
    run_id = uuid4()
    key = cache_key(run_id)
    redis_client().set(key, "[]")
    assert read_terminal_cache(run_id) is None
    assert redis_client().exists(key) == 0

    redis_client().set(key, f'{{"run_id":"{run_id}","status":"succeeded"}}')
    assert read_terminal_cache(run_id) is None
    assert redis_client().exists(key) == 0


def test_invalid_cached_view_falls_back_to_postgres(monkeypatch) -> None:
    # 即使缓存 JSON 字段齐全但类型损坏，也应删除缓存并回退 PostgreSQL。
    bad_cache = json.dumps(
        {**main.run_view("succeeded"), "created_at": "not-a-date"},
        default=str,
    )
    deleted: list[str] = []
    monkeypatch.setattr(main, "read_terminal_cache", lambda _run_id: bad_cache)
    monkeypatch.setattr(
        main, "delete_terminal_cache", lambda run_id: deleted.append(str(run_id))
    )
    monkeypatch.setattr(main, "get_run", lambda _run_id: main.run_view("succeeded"))
    monkeypatch.setattr(main, "write_terminal_cache", lambda _run: True)
    response = main.client.get(f"/api/v1/agent-runs/{main.RUN_ID}")
    assert response.status_code == 200
    assert deleted == [str(main.RUN_ID)]
