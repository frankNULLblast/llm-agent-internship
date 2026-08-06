# 教材 Day 6 对 main.py 的扩展片段（只替换 read_agent_run() 的函数体）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM 的 patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出。

from pydantic import ValidationError

from cache import delete_terminal_cache, read_terminal_cache, write_terminal_cache


def read_agent_run(run_id: UUID) -> AgentRunView:
    # 只替换原函数体；不缓存 404，否则刚创建的同一 UUID 在负缓存过期前可能一直不可见。
    cached = read_terminal_cache(run_id)
    if cached is not None:
        try:
            return AgentRunView.model_validate_json(cached)
        except ValidationError:
            delete_terminal_cache(run_id)

    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run 不存在")
    write_terminal_cache(run)
    return AgentRunView.model_validate(run)
